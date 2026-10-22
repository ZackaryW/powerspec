"""Delivery intent is observable in plans, rendering, and source lifecycle."""
import pytest

from powerspec.catalog import Catalog, ConfigurationError
from powerspec.profiles import compose
from powerspec.provisioning import plan_skills
from powerspec.skill_references import SkillReferences
from test_profiles import profile, skill, source


def test_resolve_only_union_exclusions_overlap_and_scope(tmp_path):
    skill(tmp_path, 'a', 'a')
    skill(tmp_path, 'b', 'b')
    profile(tmp_path, 'main', scope='project', profiles=['@builtin/install', '@builtin/unused'],
            **{'resolve-skills': ['@builtin/a', '@builtin/a']})
    profile(tmp_path, 'install', skills=['@builtin/a'])
    profile(tmp_path, 'unused', **{'resolve-skills': ['@builtin/b']})
    bundle = compose(Catalog(builtin=tmp_path), '@builtin/main', agent='codex',
                     exclude_profiles=['@builtin/unused'])
    assert [t.resource.ref for t in bundle.resolve_skills] == ['@builtin/a']
    assert [p.ref for p in plan_skills(bundle)] == ['@builtin/a']
    assert bundle.skills[0].scope == 'user'
    assert bundle.armed('skill', '@builtin/a')
    assert not bundle.armed('skill', '@builtin/b')


def test_deferred_native_handoff_distinguishes_delivery_intent(tmp_path):
    skill(tmp_path, 'a', 'a')
    skill(tmp_path, 'b', 'b')
    profile(tmp_path, 'main', skills=['@builtin/a'], **{'resolve-skills': ['@builtin/b']})
    catalog = Catalog(builtin=tmp_path)
    for deferred in (False, True):
        bundle = compose(catalog, '@builtin/main', agent='codex', resolve_skills=not deferred)
        references = SkillReferences(bundle, catalog=catalog)
        assert references.classify('a') == 'ordinary'
        with pytest.raises(ConfigurationError, match='pspec:b'):
            references.classify('b')


def test_resolve_only_same_names_do_not_collide_with_native_targets(tmp_path):
    one, two = tmp_path / 'one', tmp_path / 'two'
    skill(one, 'a', 'same')
    skill(two, 'b', 'same')
    profile(one, 'main', skills=['@builtin/same'],
            **{'resolve-skills': ['@builtin/same', '@other/same']})
    bundle = compose(Catalog(builtin=one, sources={'other': two}), '@builtin/main', agent='codex')
    assert len(bundle.resolve_skills) == 2
    assert len(plan_skills(bundle)) == 1


@pytest.mark.parametrize('value', ['"@builtin/a"', '[1]', '["bad"]'])
def test_strict_resolve_selection(tmp_path, value):
    path = tmp_path / 'profiles/main.toml'
    path.parent.mkdir()
    path.write_text(f'resolve-skills={value}')
    with pytest.raises(ConfigurationError):
        Catalog(builtin=tmp_path)


def test_resolve_remote_deferred_requires_recipe_without_lookup(tmp_path):
    profile(tmp_path, 'main', **{'resolve-skills': ['tools/skills/*']})
    with pytest.raises(ConfigurationError, match='missing source declaration'):
        compose(Catalog(builtin=tmp_path), '@builtin/main', agent='codex', resolve_skills=False)
    source(tmp_path, 'main', 'tools')
    def forbidden(*args):
        pytest.fail('deferred composition inspected a source')
    bundle = compose(Catalog(builtin=tmp_path, git_resolver=forbidden), '@builtin/main',
                     agent='codex', resolve_skills=False)
    assert bundle.armed('skill', 'tools/skills/*')
    assert plan_skills(bundle) == ()


def test_init_prepares_resolve_source_without_skill_writes(tmp_path, monkeypatch):
    from contextlib import contextmanager
    from powerspec.installation import install_consumer
    from powerspec.sources import SourceBinding
    from test_installation import setup
    project, builtin, remote = setup(tmp_path)
    path = builtin / 'profiles/main.toml'
    path.write_text(path.read_text().replace('skills=', 'resolve-skills='))
    calls = []
    class Store:
        def ensure(self, identity, recipe):
            calls.append(identity)
            return SourceBinding(identity, recipe['origin'], 'main', 'a'*40, 's', 'a', remote)
    @contextmanager
    def resources():
        yield builtin
    monkeypatch.setattr('powerspec.workspace.builtin_catalog_root', resources)
    from powerspec.provisioning import HookOutcome
    monkeypatch.setattr('powerspec.installation.provision_hooks',
                        lambda agent, **kw: HookOutcome(agent, 'reused'))
    home = tmp_path / 'home'
    result = install_consumer(project, agent='codex', home=home,
                              registry=tmp_path / 'registry', source_store=Store())
    assert result.ok
    assert calls == ['tools']
    assert not list(home.rglob('SKILL.md'))


def test_upgrade_refreshes_resolve_source_preserving_previous_native_copies(tmp_path):
    from test_upgrading import fixture, Store, run_upgrade
    data = fixture(tmp_path)
    before = {p: p.read_bytes() for p in data.home.rglob('*') if p.is_file() and 'skills' in p.parts}
    path = data.builtin / 'profiles/main.toml'
    path.write_text(path.read_text().replace('skills=', 'resolve-skills='))
    store = Store(data.old, data.new)
    result = run_upgrade(data, source_store=store)
    assert result.ok, result.diagnostics
    assert [method for method, *_ in store.calls] == ['lookup', 'acquire']
    assert result.removed == ()
    assert {p: p.read_bytes() for p in before} == before


def test_resolve_only_native_diagnostic_uses_bounded_metadata_lookup(tmp_path, monkeypatch):
    import powerspec.skill_references as references
    builtin, remote = tmp_path / 'builtin', tmp_path / 'remote'
    profile(builtin, 'main', **{'resolve-skills':['tools/skills/*']})
    source(builtin, 'main', 'tools')
    skill(remote, 'a', 'a')
    calls = []
    monkeypatch.setattr(references, 'monotonic', lambda: 10.0)
    def lookup(identity, recipe, *, deadline):
        calls.append((identity, deadline))
        return remote
    catalog = Catalog(builtin=builtin, git_resolver=lookup)
    bundle = compose(catalog, '@builtin/main', agent='codex', resolve_skills=False)
    with pytest.raises(ConfigurationError, match='pspec:a'):
        SkillReferences(bundle, catalog=catalog).classify('a')
    assert calls == [('tools', 11.0)]

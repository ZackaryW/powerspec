from types import SimpleNamespace
import pytest

from powerspec.catalog import Catalog, ConfigurationError, MetadataUnavailable
from powerspec.catalog_skills import select_catalog_skill, resolve_catalog_skill
from powerspec.profiles import compose
from test_profiles import skill, profile, source


def test_bare_name_needs_complete_evidence_but_exact_local_does_not(tmp_path):
    skill(tmp_path, 'a', 'a')
    profile(tmp_path, 'main', **{'resolve-skills': ['@builtin/a', 'offline/skills/*']})
    source(tmp_path, 'main', 'offline')
    calls = []
    def unavailable(*args):
        calls.append(args)
        raise MetadataUnavailable('offline source: run pspec init')
    catalog = Catalog(builtin=tmp_path, git_resolver=unavailable)
    bundle = compose(catalog, '@builtin/main', agent='codex', resolve_skills=False)
    assert select_catalog_skill(catalog, bundle, '@builtin/a').name == 'a'
    assert calls == []
    with pytest.raises(ConfigurationError, match='incomplete.*offline'):
        select_catalog_skill(catalog, bundle, 'a')
    assert len(calls) == 1


def test_git_wildcard_membership_ambiguity_declared_names_and_dedup(tmp_path):
    builtin, remote = tmp_path / 'builtin', tmp_path / 'remote'
    skill(remote, 'one', 'same')
    skill(remote, 'two', 'same')
    skill(remote, 'unused', 'unused')
    profile(builtin, 'main', **{'resolve-skills': ['tools/skills/one', 'tools/skills/two', 'tools/skills/one']})
    source(builtin, 'main', 'tools')
    catalog = Catalog(builtin=builtin, gitsources={'tools': remote})
    bundle = compose(catalog, '@builtin/main', agent='codex', resolve_skills=False)
    with pytest.raises(ConfigurationError) as error:
        select_catalog_skill(catalog, bundle, 'same')
    assert 'tools/skills/one' in str(error.value) and 'tools/skills/two' in str(error.value)
    assert select_catalog_skill(catalog, bundle, 'tools/skills/two').name == 'same'
    with pytest.raises(ConfigurationError, match='not selected'):
        select_catalog_skill(catalog, bundle, 'tools/skills/unused')
    profile(builtin, 'main', **{'resolve-skills': ['tools/skills/*']})
    source(builtin, 'main', 'tools')
    catalog = Catalog(builtin=builtin, gitsources={'tools': remote})
    bundle = compose(catalog, '@builtin/main', agent='codex')
    assert len(bundle.resolve_skills) == 3
    with pytest.raises(ConfigurationError, match='ambiguous'):
        select_catalog_skill(catalog, bundle, 'same')
    assert select_catalog_skill(catalog, bundle, 'tools/skills/one').name == 'same'
    with pytest.raises(ConfigurationError, match='not selected'):
        select_catalog_skill(catalog, bundle, 'tools/skills/one/deeper')
    profile(builtin, 'main', skills=['tools/skills/one'], **{'resolve-skills':['tools/skills/one']})
    source(builtin, 'main', 'tools')
    catalog = Catalog(builtin=builtin, gitsources={'tools':remote})
    bundle = compose(catalog, '@builtin/main', agent='codex')
    assert select_catalog_skill(catalog, bundle, 'same').ref == 'tools/skills/one'


def test_editable_origins_survive_cleanup_and_do_not_mix_trees(tmp_path, monkeypatch):
    import powerspec.resources as resources
    from test_skill_cli import put
    checkout, installed = tmp_path / 'checkout', tmp_path / 'installed'
    for root, name, body in [(checkout, 'authored', 'LIVE'), (installed,'authored','STALE'), (installed,'upstream','PACKAGED')]:
        put(root / f'skills/{name}/SKILL.md', f'---\nname: {name}\n---\n{body}')
        put(root / f'skills/{name}/references/detail.md', body)
    profile(checkout, 'main', **{'resolve-skills':['@builtin/authored','@builtin/upstream']})
    monkeypatch.setattr(resources, 'files', lambda _: tmp_path / 'missing')
    monkeypatch.setattr(resources, '_checkout_catalog_root', lambda: checkout)
    monkeypatch.setattr(resources, '_distribution_catalog_root', lambda: installed)
    with resources.builtin_catalog_root() as merged:
        catalog = Catalog(builtin=merged)
        bundle = compose(catalog, '@builtin/main', agent='codex', resolve_skills=False)
        workspace = SimpleNamespace(catalog=catalog, bundle=bundle, consumer=None)
        authored = resolve_catalog_skill(workspace, 'authored')
        upstream = resolve_catalog_skill(workspace, 'upstream')
    assert not merged.exists()
    assert authored.root == checkout / 'skills/authored'
    assert upstream.root == installed / 'skills/upstream'
    for result, expected in [(authored,'LIVE'), (upstream,'PACKAGED')]:
        assert result.resolution.content.endswith(expected+'\n')
        assert (result.root / 'references/detail.md').read_text() == expected
    # A manifest requesting a missing authored file must not borrow installed data.
    put(checkout / 'skills/authored/pspec.toml', 'version=2\nentry="references/missing.md"')
    put(installed / 'skills/authored/references/missing.md', 'STALE FALLBACK')
    with resources.builtin_catalog_root() as merged:
        catalog = Catalog(builtin=merged)
        workspace.catalog = catalog
        with pytest.raises(ConfigurationError, match='unavailable'):
            resolve_catalog_skill(workspace, 'authored')


def test_transient_only_provider_rejected(tmp_path):
    from powerspec.resources import _origin_scope, durable_skill_root
    skill(tmp_path, 'one', 'one')
    with _origin_scope(tmp_path, None):
        with pytest.raises(ConfigurationError, match='transient-only'):
            durable_skill_root(tmp_path / 'skills/one/SKILL.md')

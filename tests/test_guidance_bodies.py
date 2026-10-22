from pathlib import Path

import pytest
from ruamel.yaml import YAML

from powerspec.catalog import Catalog, ConfigurationError


def put(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


def test_context_and_trait_share_contained_body(tmp_path):
    body = 'When history matters, use <skill:zmem-query-memory>.\n'
    put(tmp_path, 'guidance/memory.md', body)
    put(tmp_path, 'contexts/memory.toml', '[[attach.context]]\nbody_file="guidance/memory.md"')
    put(tmp_path, 'traits/memory.toml', 'hooks=["sessionStart"]\nbody_file="guidance/memory.md"')
    catalog = Catalog(builtin=tmp_path)
    assert catalog.get('context', '@builtin/memory').data['attach']['context'][0]['body'] == body
    assert catalog.get('trait', '@builtin/memory').data['body'] == body


@pytest.mark.parametrize('body', [
    '', 'body="inline"\nbody_file="guidance.md"', 'body_file="../outside.md"',
    'body_file="/absolute.md"', 'body_file="missing.md"', 'body_file=""',
])
def test_invalid_body_source_is_located(tmp_path, body):
    put(tmp_path, 'traits/memory.toml', 'hooks=["sessionStart"]\n' + body)
    with pytest.raises(ConfigurationError, match='memory.toml'):
        Catalog(builtin=tmp_path)


def test_invalid_utf8_is_located(tmp_path):
    put(tmp_path, 'traits/memory.toml', 'hooks=["sessionStart"]\nbody_file="body.md"')
    (tmp_path / 'body.md').write_bytes(b'\xff')
    with pytest.raises(ConfigurationError, match='memory.toml'):
        Catalog(builtin=tmp_path)


def test_escaping_body_link_is_rejected(tmp_path):
    root = tmp_path / 'catalog'
    put(root, 'traits/memory.toml', 'hooks=["sessionStart"]\nbody_file="body.md"')
    outside = put(tmp_path, 'outside.md', 'outside')
    try:
        (root / 'body.md').symlink_to(outside)
    except OSError:
        pytest.skip('symlink creation unavailable')
    with pytest.raises(ConfigurationError, match='escapes'):
        Catalog(builtin=root)


@pytest.mark.parametrize('event', ['sessionStart', 'afterCompaction'])
def test_standing_rule_survives_missing_sources_and_tools(tmp_path, event):
    from powerspec.catalog import MetadataUnavailable
    from powerspec.hooks import dispatch
    from powerspec.profiles import compose

    authored = Path(__file__).resolve().parents[1] / '.pspec'
    root = tmp_path / 'catalog'
    for name in ('profiles/zmem-lifecycle.toml', 'traits/zmem-lifecycle.toml',
                 'contexts/incremental-checkpoints.toml', 'contexts/zmem-lifecycle.toml'):
        put(root, name, (authored / name).read_text())
    put(root, 'guidance/zmem-lifecycle.md',
        'Memory policy fixture: use <skill:zmem-query-memory>.\n\nKeep this second paragraph.\n')
    project = tmp_path / 'project'
    (project / '.git').mkdir(parents=True)
    put(project, 'openspec/.pspec/config.toml', '[vars]\n')
    def missing(*a, **k):
        raise MetadataUnavailable('no selected materialization; run init')
    catalog = Catalog(builtin=root, git_resolver=missing)
    # The contract here is delivery of the selected body despite unavailable
    # tools/sources, not the particular prose chosen for the memory policy.
    expected_body = 'Memory policy fixture: use zmem-query-memory.\n\nKeep this second paragraph.'
    diagnostics = []
    result = dispatch(logical_event=event, agent='codex', cwd=project,
                      catalog=catalog, env={'PATH': ''}, diagnostics=diagnostics)
    assert result and expected_body in result
    assert any('no selected materialization' in item for item in diagnostics)
    bundle = compose(catalog, agent='codex', resolve_skills=False)
    assert '@builtin/zmem-lifecycle' in [item.ref for item in bundle.contexts]
    from powerspec.conditions import context_contributions, Invocation
    from powerspec.syncing import publish
    target = put(project, 'openspec/config.yaml', 'schema: spec-driven\n')
    publish(target, context_contributions(bundle, None, Invocation(project, env={'PATH': ''})))
    published = YAML(typ='safe').load(target.read_text())
    assert published['schema'] == 'spec-driven'
    assert expected_body in published['context']
    excluded = compose(catalog, agent='codex', resolve_skills=False,
                       exclude_profiles=['@builtin/zmem-lifecycle'])
    assert not excluded.contexts and not excluded.traits
    put(project, 'openspec/.pspec/config.toml',
        'exclude-profiles=["@builtin/zmem-lifecycle"]\n[vars]\n')
    assert dispatch(logical_event=event, agent='codex', cwd=project,
                    catalog=catalog, env={'PATH': ''}) is None
    publish(target, context_contributions(excluded, None, Invocation(project, env={'PATH': ''})))
    republished = YAML(typ='safe').load(target.read_text())
    assert republished['schema'] == 'spec-driven'
    assert expected_body not in republished.get('context', '')


def test_memory_profile_uses_zmem2_with_stable_native_names(tmp_path):
    from powerspec.profiles import compose
    from powerspec.sources import SourceBinding

    authored = Path(__file__).resolve().parents[1] / '.pspec'
    root = tmp_path / 'catalog'
    for name in ('profiles/zmem-lifecycle.toml', 'traits/zmem-lifecycle.toml',
                 'contexts/incremental-checkpoints.toml', 'contexts/zmem-lifecycle.toml',
                 'guidance/zmem-lifecycle.md'):
        put(root, name, (authored / name).read_text())
    remote = tmp_path / 'remote'
    names = {'zmem-query-memory', 'zmem-author-commits', 'zmem-design-extensions'}
    for name in names:
        put(remote, f'skills/{name}/SKILL.md',
            f'---\nname: {name}\ndescription: Memory workflow.\n---\n')
    seen = []
    def resolve(identity, recipe):
        seen.append((identity, dict(recipe)))
        assert identity == 'zmem'
        assert recipe == dict(provider='git', origin='https://github.com/ZackaryW/zmem2', reference='main')
        return SourceBinding(identity, recipe['origin'], 'main', 'a' * 40, 'source', 'output', remote)
    catalog = Catalog(builtin=root, git_resolver=resolve)
    bundle = compose(catalog, agent='codex', project_root=tmp_path)
    assert {target.resource.name for target in bundle.skills} == names
    assert all(target.scope == 'user' and target.profile == '@builtin/zmem-lifecycle'
               for target in bundle.skills)
    assert seen
    seen.clear()
    excluded = compose(Catalog(builtin=root, git_resolver=resolve), agent='codex',
                       exclude_profiles=['@builtin/zmem-lifecycle'])
    assert not excluded.skills and not excluded.contexts and not excluded.traits
    assert not seen

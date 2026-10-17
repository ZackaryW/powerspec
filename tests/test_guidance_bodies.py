from pathlib import Path

import pytest

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
                 'contexts/incremental-checkpoints.toml', 'contexts/zmem-lifecycle.toml',
                 'guidance/zmem-lifecycle.md'):
        put(root, name, (authored / name).read_text())
    project = tmp_path / 'project'
    (project / '.git').mkdir(parents=True)
    put(project, 'openspec/.pspec/config.toml', '[vars]\n')
    def missing(*a, **k):
        raise MetadataUnavailable('no selected materialization; run init')
    catalog = Catalog(builtin=root, git_resolver=missing)
    diagnostics = []
    result = dispatch(logical_event=event, agent='codex', cwd=project,
                      catalog=catalog, env={'PATH': ''}, diagnostics=diagnostics)
    assert result and 'zmem-query-memory' in result
    assert 'without asking the user to name zmem' in result
    assert 'unavailable' in result
    assert any('no selected materialization' in item for item in diagnostics)
    bundle = compose(catalog, agent='codex', resolve_skills=False)
    assert '@builtin/zmem-lifecycle' in [item.ref for item in bundle.contexts]
    from powerspec.conditions import context_contributions, Invocation
    from powerspec.syncing import publish
    target = put(project, 'openspec/config.yaml', 'schema: spec-driven\n')
    publish(target, context_contributions(bundle, None, Invocation(project, env={'PATH': ''})))
    assert 'before forming a conclusion' in target.read_text()
    assert '<skill:' not in target.read_text()
    excluded = compose(catalog, agent='codex', resolve_skills=False,
                       exclude_profiles=['@builtin/zmem-lifecycle'])
    assert not excluded.contexts and not excluded.traits

"""MilkpanSources against an in-memory milkpan: mapping, two-phase publication, release."""
import pytest

from powerspec.catalog import ConfigurationError, MetadataUnavailable
from powerspec.sources import MilkpanSources, milkpan_spec

from milkpan_fake import FakeMilkpan


RECIPE = {'provider': 'git', 'origin': 'https://github.com/Octo/Tools.git', 'reference': 'main'}
A, B = 'a' * 40, 'b' * 40


@pytest.fixture
def fake(tmp_path):
    client = FakeMilkpan(tmp_path / 'milkpan')
    client.refs['github:octo/tools@main'] = A
    return client


def store(fake, tmp_path, name='consumer'):
    config = tmp_path / name / 'openspec/.pspec/config.toml'
    config.parent.mkdir(parents=True, exist_ok=True)
    return MilkpanSources(fake, consumer_path=config)


def test_origins_map_to_github_and_local_specs(tmp_path):
    assert milkpan_spec('https://github.com/Octo/Tools.git') == 'github:octo/tools'
    local = tmp_path / 'repo'
    assert milkpan_spec(str(local)) == 'local:' + str(local.resolve()).replace('\\', '/')
    assert milkpan_spec(local.resolve().as_uri()) == 'local:' + str(local.resolve()).replace('\\', '/')
    with pytest.raises(ConfigurationError, match='milkpan supports'):
        milkpan_spec('https://gitlab.com/team/tools')


def test_selection_is_published_only_on_commit(fake, tmp_path):
    sources = store(fake, tmp_path)
    binding = sources.ensure('tools', RECIPE)
    assert binding.resolved_revision == A and binding.root.is_dir()
    assert ('acquire', 'github:octo/tools@main', sources.scope + '-candidates') in fake.calls
    assert ('acquire', f'github:octo/tools@{A}', sources.scope) in fake.calls
    with pytest.raises(MetadataUnavailable):
        sources.lookup('tools', RECIPE)
    sources.commit()
    assert sources.lookup('tools', RECIPE).resolved_revision == A


def test_refresh_replaces_and_releases_the_old_commit_lease(fake, tmp_path):
    sources = store(fake, tmp_path)
    sources.ensure('tools', RECIPE)
    sources.commit()
    old = sources.lookup('tools', RECIPE).artifact_id
    fake.refs['github:octo/tools@main'] = B
    refreshed = sources.acquire('tools', RECIPE)
    assert refreshed.resolved_revision == B
    assert sources.lookup('tools', RECIPE).resolved_revision == A, 'still the old selection until commit'
    sources.commit()
    assert sources.lookup('tools', RECIPE).resolved_revision == B
    assert ('release', old) in fake.calls


def test_reject_keeps_the_previous_selection(fake, tmp_path):
    sources = store(fake, tmp_path)
    sources.ensure('tools', RECIPE)
    sources.commit()
    fake.refs['github:octo/tools@main'] = B
    candidate = sources.acquire('tools', RECIPE).artifact_id
    sources.reject()
    assert sources.lookup('tools', RECIPE).resolved_revision == A
    assert ('release', candidate) in fake.calls


def test_consumers_update_independently_and_share_content(fake, tmp_path):
    first, second = store(fake, tmp_path, 'one'), store(fake, tmp_path, 'two')
    for sources in (first, second):
        sources.ensure('tools', RECIPE)
        sources.commit()
    assert len(fake.stored) == 1, 'one stored commit serves both consumers'
    fake.refs['github:octo/tools@main'] = B
    first.acquire('tools', RECIPE)
    first.commit()
    assert first.lookup('tools', RECIPE).resolved_revision == B
    assert second.lookup('tools', RECIPE).resolved_revision == A


def test_commit_references_are_checked(fake, tmp_path):
    sources = store(fake, tmp_path)
    fake.refs[f'github:octo/tools@{A}'] = A
    pinned = dict(RECIPE, reference=A)
    assert sources.ensure('tools', pinned).resolved_revision == A


def test_lookup_never_mutates(fake, tmp_path):
    sources = store(fake, tmp_path)
    sources.ensure('tools', RECIPE)
    sources.commit()
    before = list(fake.calls)
    sources.lookup('tools', RECIPE)
    assert fake.calls == before


def test_moved_consumers_and_corrupt_state_are_not_repaired(fake, tmp_path):
    sources = store(fake, tmp_path)
    sources.ensure('tools', RECIPE)
    sources.commit()
    state = sources.state_path.read_text(encoding='utf-8')
    sources.state_path.write_text(state.replace(sources.scope, 'consumer-elsewhere'), encoding='utf-8')
    with pytest.raises(ConfigurationError, match='consumer moved'):
        sources.lookup('tools', RECIPE)
    sources.state_path.write_text('{not json', encoding='utf-8')
    with pytest.raises(ConfigurationError, match='invalid milkpan selection state'):
        sources.lookup('tools', RECIPE)
    assert sources.state_path.read_text(encoding='utf-8') == '{not json'


def test_concurrent_writers_are_refused(fake, tmp_path):
    sources = store(fake, tmp_path)
    lock = sources.state_path.with_suffix('.lock')
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text('1234', encoding='utf-8')
    with pytest.raises(ConfigurationError, match='already in progress'):
        sources.ensure('tools', RECIPE)


def test_exhausted_lookup_deadlines_never_call_milkpan(fake, tmp_path):
    import time
    sources = store(fake, tmp_path)
    sources.ensure('tools', RECIPE)
    sources.commit()
    with pytest.raises(MetadataUnavailable, match='deadline'):
        sources.lookup('tools', RECIPE, deadline=time.monotonic() - 1)


def test_scopes_are_namespaced_and_earlier_selections_need_init(fake, tmp_path):
    import json
    sources = store(fake, tmp_path)
    assert sources.scope.startswith('powerspec/consumer-')
    earlier = {'consumer': str(sources.consumer_path), 'scope': sources.scope.removeprefix('powerspec/'),
               'selected': {'x': {'lease': 'old'}}}
    sources.state_path.parent.mkdir(parents=True, exist_ok=True)
    sources.state_path.write_text(json.dumps(earlier), encoding='utf-8')
    with pytest.raises(MetadataUnavailable, match='run init'):
        sources.lookup('tools', RECIPE)
    sources.ensure('tools', RECIPE)
    sources.commit()
    assert json.loads(sources.state_path.read_text(encoding='utf-8'))['scope'] == sources.scope

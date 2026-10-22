"""Real provider cache boundaries, with no public network or wall-clock sleeps."""
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile

import pytest
from saucepan_sdk import Client
from saucepan_sdk.transport import CliTransport

from powerspec.catalog import ConfigurationError
from powerspec.sources import SaucepanSources
from test_sources_integration import BINARY, git

pytestmark = pytest.mark.skipif(not BINARY, reason='set SAUCEPAN_TEST_BINARY')


class ClockTransport(CliTransport):
    now = 1_800_000_000

    def json(self, config, call):
        return super().json(config, replace(call, argv=(*call.argv, '--test-now', str(self.now))))


@pytest.fixture
def cache_case(monkeypatch):
    with tempfile.TemporaryDirectory(prefix='ps-ttl-') as temporary:
        root = Path(temporary)
        repo = root / 'origin'
        repo.mkdir()
        git(repo, 'init', '-b', 'main')
        git(repo, 'config', 'user.name', 'Test')
        git(repo, 'config', 'user.email', 'test@example.invalid')
        (repo / 'data').write_text('A')
        git(repo, 'add', '.')
        git(repo, 'commit', '-m', 'A')
        trace = root / 'git.jsonl'
        monkeypatch.setenv('GIT_TRACE2_EVENT', str(trace))
        transport = ClockTransport()
        client = Client(executable=BINARY, root=str(root / 'store'), transport=transport)
        recipe = dict(provider='git', origin=str(repo), reference='main')
        a = SaucepanSources(client, consumer_path=root / 'a/config.toml')
        original = a.ensure('tools', recipe)
        a.commit()
        assert network_ops(trace)
        trace.write_text('')
        yield root, repo, trace, transport, client, recipe, a, original


def network_ops(trace):
    return [event['argv'] for line in trace.read_text().splitlines()
            if (event := json.loads(line)).get('event') == 'start'
            and any(verb in event['argv'] for verb in ('clone', 'fetch', 'ls-remote', 'pull'))]


@pytest.mark.parametrize('age,refresh', [(86399, False), (86400, True), (-1, True)])
def test_new_consumer_obeys_provider_cache_age(cache_case, age, refresh):
    root, repo, trace, clock, client, recipe, a, original = cache_case
    (repo / 'data').write_text('B')
    git(repo, 'commit', '-am', 'B')
    clock.now += age
    b = SaucepanSources(client, consumer_path=root / 'b/config.toml')
    selected = b.ensure('tools', recipe)
    b.commit()
    assert bool(network_ops(trace)) is refresh
    assert (selected.root / 'data').read_text() == ('B' if refresh else 'A')
    assert a.lookup('tools', recipe).resolved_revision == original.resolved_revision
    assert a._state()['selected'].values() != b._state()['selected'].values()
    trace.write_text('')
    clock.now += 100000
    assert a.ensure('tools', recipe) == original
    assert not network_ops(trace)


@pytest.mark.parametrize('age,success', [(86399, True), (86400, False)])
def test_offline_cache_eligibility(cache_case, age, success):
    root, repo, trace, clock, client, recipe, a, original = cache_case
    # Both paths are children of this test's explicitly created disposable root.
    offline = root / 'offline'
    repository_data = repo / '.git'
    assert repository_data.resolve().is_relative_to(root.resolve())
    assert offline.resolve().parent == root.resolve()
    repository_data.rename(offline)
    clock.now += age
    b = SaucepanSources(client, consumer_path=root / 'b/config.toml')
    if success:
        selected = b.ensure('tools', recipe)
        b.commit()
        assert selected.resolved_revision == original.resolved_revision
        assert not network_ops(trace)
    else:
        with pytest.raises(ConfigurationError):
            b.ensure('tools', recipe)
        assert not b._state()['selected']
    assert a.lookup('tools', recipe) == original


def test_explicit_refresh_bypasses_warm_cache_and_preserves_other_pin(cache_case):
    root, repo, trace, clock, client, recipe, a, original = cache_case
    b = SaucepanSources(client, consumer_path=root / 'b/config.toml')
    b.ensure('tools', recipe)
    b.commit()
    assert not network_ops(trace)
    (repo / 'data').write_text('B')
    git(repo, 'commit', '-am', 'B')
    clock.now += 1
    candidate = a.acquire('tools', recipe)
    assert network_ops(trace)
    assert a.lookup('tools', recipe) == original
    a.commit()
    assert (candidate.root / 'data').read_text() == 'B'
    assert b.lookup('tools', recipe).resolved_revision == original.resolved_revision

"""Consumer acceptance of provider ownership, independent of release discovery."""
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from powerspec import saucepan_tool as tool
from powerspec.catalog import ConfigurationError


@pytest.fixture
def shared(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: tmp_path))
    monkeypatch.delenv('POWERSPEC_SAUCEPAN', raising=False)
    target = tool.saucepan_executable_path()
    target.parent.mkdir(parents=True)
    target.write_bytes(b'old raw manager')
    return target


def test_compatible_raw_default_is_not_managed_readiness(shared, monkeypatch):
    monkeypatch.setattr(tool, '_probe', lambda *a, **k: '0.10.0')
    with pytest.raises(ConfigurationError, match='migration') as error:
        tool.inspect_saucepan_binary()
    assert hashlib.sha256(shared.read_bytes()).hexdigest() in str(error.value)
    assert shared.read_bytes() == b'old raw manager'


def test_explicit_override_is_standalone_even_at_shared_path(shared, monkeypatch):
    monkeypatch.setattr(tool, '_probe', lambda *a, **k: '0.10.0')
    monkeypatch.setattr(tool, '_validate', lambda *a, **k: None)
    monkeypatch.setenv('POWERSPEC_SAUCEPAN', str(shared))
    assert tool.inspect_saucepan_binary() == shared


def observation(target, state='ready', **changes):
    return dict(schema_version=1, root=str(target.parent.parent), state=state,
                launcher_path=str(target), app=str(uuid4()), claim=str(uuid4()),
                output=str(uuid4()), installed_version='v0.11.0', operation=None,
                diagnostics=[], **changes)


@pytest.mark.parametrize('state', ['ready', 'unmanaged', 'pending', 'conflict', 'absent'])
def test_managed_states_preserve_cache_and_never_discover(shared, monkeypatch, state):
    cache = shared.with_name('saucepan-check.json')
    cache.write_bytes(b'obsolete cache')
    monkeypatch.setattr(tool, '_probe', lambda *a, **k: '0.11.0+v0.11.0')
    monkeypatch.setattr(tool, '_inspect', lambda *a, **k: SimpleNamespace(ok=True, stdout=json.dumps(observation(shared, state))))
    monkeypatch.setattr('urllib.request.urlopen', lambda *a, **k: pytest.fail('release discovery'))
    if state == 'ready':
        assert tool.ensure_saucepan_binary() == shared
    else:
        with pytest.raises(ConfigurationError, match='migration' if state == 'unmanaged' else state):
            tool.ensure_saucepan_binary()
    assert cache.read_bytes() == b'obsolete cache'


@pytest.mark.parametrize('changes', [dict(schema_version=True), dict(schema_version=2), dict(app=None),
    dict(app='not-uuid'), dict(root='relative'), dict(launcher_path='elsewhere'), dict(installed_version='v0.11.1')])
def test_malformed_or_mismatched_status_is_rejected(shared, monkeypatch, changes):
    value = observation(shared)
    value.update(changes)
    monkeypatch.setattr(tool, '_probe', lambda *a, **k: '0.11.0')
    monkeypatch.setattr(tool, '_inspect', lambda *a, **k: SimpleNamespace(ok=True, stdout=json.dumps(value)))
    with pytest.raises(ConfigurationError):
        tool.inspect_saucepan_binary()


def test_readonly_version_and_status_share_one_budget(shared, monkeypatch):
    clock, calls = [1.0], []
    monkeypatch.setattr(tool, 'monotonic', lambda: clock[0])
    def inspect(argv, **options):
        calls.append((argv[-1], options['timeout']))
        clock[0] += .3
        return SimpleNamespace(ok=True, version='0.11.0', stdout=json.dumps(observation(shared)))
    monkeypatch.setattr(tool, 'inspect_executable', inspect)
    assert tool.inspect_saucepan_binary(deadline=2) == shared
    assert [x[0] for x in calls] == ['--version', 'setup-status']
    assert [x[1] for x in calls] == pytest.approx([1, .7])
    with pytest.raises(ConfigurationError, match='budget'):
        tool.inspect_saucepan_binary(deadline=1)
    assert len(calls) == 2


def test_production_provider_is_immutable_and_platform_specific():
    from dataclasses import replace
    from powerspec.saucepan_provider import PROVIDER
    assert PROVIDER.installer('Windows', 'ARM64')[0] == 'install.ps1'
    assert PROVIDER.installer('Darwin', 'arm64')[0] == 'install.sh'
    with pytest.raises(ValueError, match='platform'):
        PROVIDER.installer('Linux', 'arm64')
    for changes in (dict(tag='latest'), dict(sdk_revision='0' * 40), dict(windows_sha256='TODO'),
                    dict(release_base='https://example.com')):
        with pytest.raises(ValueError):
            replace(PROVIDER, **changes)
    fixture = replace(PROVIDER, release_base='http://127.0.0.1:1234/releases', fixture_api='http://127.0.0.1:1234')
    assert fixture.installer('Linux', 'x86_64')[1].startswith('http://127.0.0.1:1234/')


@pytest.mark.skipif(os.name != 'nt', reason='Windows provider canonical paths')
def test_windows_provider_extended_paths_match_the_same_target(shared):
    from powerspec.saucepan_provider import SetupStatus
    value = observation(shared)
    value['root'] = '\\\\?\\' + value['root']
    value['launcher_path'] = '\\\\?\\' + value['launcher_path']
    SetupStatus.model_validate(value).check_target(shared)


def test_incompatible_ready_manager_blocks_source_calls_with_explicit_update_guidance(shared, monkeypatch):
    from powerspec import sources
    value = observation(shared)
    value['installed_version'] = 'v0.12.0'
    monkeypatch.setattr(tool, '_probe', lambda *a, **k: '0.12.0')
    monkeypatch.setattr(tool, '_inspect', lambda *a, **k: SimpleNamespace(ok=True, stdout=json.dumps(value)))
    monkeypatch.setattr(sources, 'Client', lambda **k: pytest.fail('source client created before readiness'))
    monkeypatch.setattr('urllib.request.urlopen', lambda *a, **k: pytest.fail('incompatible manager downloaded'))
    with pytest.raises(ConfigurationError, match='self-update') as error:
        sources.SaucepanSources()._client_or_default()
    assert value['app'] in str(error.value) and value['claim'] in str(error.value)
    assert shared.read_bytes() == b'old raw manager'


def test_corrupt_status_does_not_provision(shared, monkeypatch):
    monkeypatch.setattr(tool, '_probe', lambda *a, **k: '0.11.0')
    monkeypatch.setattr(tool, '_inspect', lambda *a, **k: SimpleNamespace(ok=True, stdout='{malformed'))
    monkeypatch.setattr('urllib.request.urlopen', lambda *a, **k: pytest.fail('corrupt status download'))
    with pytest.raises(ConfigurationError, match='JSON'):
        tool.ensure_saucepan_binary()

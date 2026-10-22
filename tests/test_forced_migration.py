import hashlib
from pathlib import Path

import pytest

from powerspec import saucepan_bootstrap as bootstrap, saucepan_tool as tool
from powerspec.catalog import ConfigurationError
from test_managed_setup_contract import shared, observation
from powerspec.saucepan_provider import SetupStatus


def test_forced_raw_manager_supplies_observed_digest(shared, monkeypatch):
    monkeypatch.setattr(tool, '_probe', lambda *a, **k: '0.10.0')
    seen = []
    monkeypatch.setattr(bootstrap, 'ensure_default', lambda target, **kw: seen.append(kw) or target)
    assert tool.ensure_saucepan_binary(migrate_unmanaged=True) == shared
    assert seen == [{'expected_sha256': hashlib.sha256(shared.read_bytes()).hexdigest()}]


@pytest.mark.parametrize('state', ['ready', 'pending', 'conflict'])
def test_force_does_not_migrate_managed_states(shared, monkeypatch, state):
    monkeypatch.setattr(tool, '_probe', lambda *a, **k: '0.11.0')
    monkeypatch.setattr(tool, 'inspect_managed_status', lambda *a, **k: SetupStatus.model_validate(observation(shared, state)))
    monkeypatch.setattr(bootstrap, 'ensure_default', lambda *a, **k: pytest.fail('unexpected migration'))
    if state == 'ready':
        assert tool.ensure_saucepan_binary(migrate_unmanaged=True) == shared
    else:
        with pytest.raises(ConfigurationError, match=state):
            tool.ensure_saucepan_binary(migrate_unmanaged=True)


def test_force_does_not_adopt_standalone(shared, monkeypatch):
    monkeypatch.setenv('POWERSPEC_SAUCEPAN', str(shared))
    monkeypatch.setattr(tool, '_probe', lambda *a, **k: '0.10.0')
    monkeypatch.setattr(tool, '_validate', lambda *a, **k: None)
    monkeypatch.setattr(bootstrap, 'ensure_default', lambda *a, **k: pytest.fail('adopted override'))
    assert tool.ensure_saucepan_binary(migrate_unmanaged=True) == shared


@pytest.mark.parametrize('launcher_survives', [True, False])
def test_uncertain_migration_cannot_be_replayed(shared, monkeypatch, launcher_survives):
    monkeypatch.setattr(tool, '_probe', lambda *a, **k: '0.10.0')
    monkeypatch.setattr(bootstrap.shutil, 'which', lambda _: 'shell')
    monkeypatch.setattr(bootstrap, '_download', lambda url, path, digest: path.write_text('verified fixture'))
    seen = []
    def run(argv, target, operation):
        seen.append((argv, operation))
        assert hashlib.sha256(b'old raw manager').hexdigest() in argv
        assert '-MigrateUnmanaged' in argv or '--migrate-unmanaged' in argv
        if not launcher_survives:
            target.unlink()
        raise bootstrap.SetupFailure('response lost; mutation may have committed', root=target.parent.parent, operation=operation)
    monkeypatch.setattr(bootstrap, 'run_installer', run)
    with pytest.raises(ConfigurationError, match='response lost'):
        tool.ensure_saucepan_binary(migrate_unmanaged=True)
    with pytest.raises(ConfigurationError, match=seen[0][1]):
        tool.ensure_saucepan_binary(migrate_unmanaged=True)
    assert len(seen) == 1


def test_forced_migration_does_not_reinterpret_unknown_version(shared, monkeypatch):
    monkeypatch.setattr(tool, '_probe', lambda *a, **k: 'unknown')
    monkeypatch.setattr(bootstrap, 'ensure_default', lambda *a, **k: pytest.fail('unknown file migrated'))
    with pytest.raises(ConfigurationError):
        tool.ensure_saucepan_binary(migrate_unmanaged=True)

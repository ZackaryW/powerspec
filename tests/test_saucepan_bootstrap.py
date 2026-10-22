"""Official installer boundary; failures retain provider evidence and never retry."""
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
from uuid import uuid4

import pytest

from powerspec import saucepan_bootstrap as bootstrap
from powerspec.catalog import ConfigurationError
from test_managed_setup_contract import observation


def outcome(target, operation, status='complete'):
    value = observation(target)
    value.pop('state')
    return dict(value, status=status, changed=status == 'complete', operation=operation,
                lifecycle_operation=None, backup_paths=[], retry_shim=None)


def test_installer_exit_two_retains_receipt_and_does_not_retry(tmp_path, monkeypatch, capsys):
    target = tmp_path / 'home/.saucepan/bin/saucepan.exe'
    operation = str(uuid4())
    calls = []
    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=2, stdout=json.dumps(outcome(target, operation, 'failed')), stderr='provider progress\n')
    monkeypatch.setattr(subprocess, 'run', run)
    # Public first-use boundary must preserve exit-2 output, not downgrade to launch failure.
    with pytest.raises(ConfigurationError, match=operation):
        bootstrap.run_installer(['fixture', str(target)], target, operation)
    assert len(calls) == 1
    assert calls[0][1]['shell'] is False
    assert calls[0][1]['timeout'] > 0
    captured = capsys.readouterr()
    assert captured.out == '' and 'provider progress' in captured.err

@pytest.mark.parametrize('status', ['preparing', 'commit_intent', 'cleanup_pending', 'failed', 'conflict'])
def test_noncomplete_receipts_preserve_backup_and_retry(tmp_path, monkeypatch, status):
    target, operation = tmp_path / 'store/bin/saucepan', str(uuid4())
    value = outcome(target, operation, status)
    value.update(backup_paths=['preserved-original'], retry_shim='durable-shim')
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=2, stdout=json.dumps(value), stderr=''))
    with pytest.raises(bootstrap.SetupFailure) as error:
        bootstrap.run_installer(['fixture'], target, operation)
    assert error.value.outcome.status == status
    assert error.value.outcome.backup_paths == ['preserved-original']
    assert 'durable-shim' in str(error.value)


@pytest.mark.parametrize('failure', ['timeout', 'empty', 'wrong-operation', 'wrong-exit', 'wrong-root'])
def test_uncertain_results_report_original_operation_without_retry(tmp_path, monkeypatch, failure):
    target, operation = tmp_path / 'store/bin/saucepan', str(uuid4())
    calls = []
    def run(argv, **kwargs):
        calls.append(argv)
        if failure == 'timeout':
            raise subprocess.TimeoutExpired(argv, 1, stderr=b'last progress')
        value = outcome(target, operation)
        if failure == 'wrong-operation':
            value['operation'] = str(uuid4())
        if failure == 'wrong-root':
            value['root'] = str(tmp_path / 'other')
        return SimpleNamespace(returncode=2 if failure == 'wrong-exit' else 0,
                               stdout='' if failure == 'empty' else json.dumps(value), stderr='')
    monkeypatch.setattr(subprocess, 'run', run)
    with pytest.raises(bootstrap.SetupFailure, match='may have committed') as error:
        bootstrap.run_installer(['fixture'], target, operation)
    assert error.value.operation == operation and error.value.root == target.parent.parent
    assert len(calls) == 1 and not target.parent.parent.exists()


def test_verified_installer_stages_externally_and_reinspects_complete(tmp_path, monkeypatch):
    from powerspec import saucepan_tool as tool
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: tmp_path))
    monkeypatch.delenv('POWERSPEC_SAUCEPAN', raising=False)
    target = tool.saucepan_executable_path()
    monkeypatch.setattr(bootstrap.shutil, 'which', lambda name: 'shell')
    staged, inspected = [], []
    def download(url, path, digest):
        assert not path.is_relative_to(target.parent.parent)
        path.write_text('verified fixture')
        staged.append(path)
    monkeypatch.setattr(bootstrap, '_download', download)
    def run(argv, target, operation):
        assert 'ExecutionPolicy' not in ' '.join(argv)
        assert 'MigrateUnmanaged' not in ' '.join(argv)
        assert operation in argv and str(target.parent.parent) in argv
        # Only the provider creates anything in its root.
        target.parent.mkdir(parents=True)
        target.write_bytes(b'provider-owned')
        return bootstrap.SetupOutcome.model_validate(outcome(target, operation))
    monkeypatch.setattr(bootstrap, 'run_installer', run)
    monkeypatch.setattr(tool, 'inspect_saucepan_binary', lambda path: inspected.append(path) or path)
    assert bootstrap.ensure_default(target) == target
    assert inspected == [target] and all(not path.exists() for path in staged)


def test_bad_checksum_never_executes_or_writes_store(tmp_path, monkeypatch):
    import io
    target = tmp_path / 'store/bin/saucepan'
    monkeypatch.setattr(bootstrap.shutil, 'which', lambda name: 'shell')
    monkeypatch.setattr(bootstrap.urllib.request, 'urlopen', lambda *a, **k: io.BytesIO(b'tampered'))
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: pytest.fail('unverified execution'))
    with pytest.raises(ConfigurationError, match='checksum'):
        bootstrap.ensure_default(target)
    assert not target.parent.parent.exists()


def test_missing_shell_provides_manual_setup_without_download(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap.shutil, 'which', lambda name: None)
    monkeypatch.setattr(bootstrap.urllib.request, 'urlopen', lambda *a, **k: pytest.fail('download before prerequisites'))
    with pytest.raises(ConfigurationError, match='missing.*prerequisite'):
        bootstrap.ensure_default(tmp_path / 'store/bin/saucepan')


def test_override_missing_is_never_installed(tmp_path, monkeypatch):
    from powerspec import saucepan_tool as tool
    target = tmp_path / 'missing/saucepan'
    monkeypatch.setenv('POWERSPEC_SAUCEPAN', str(target))
    monkeypatch.setattr(bootstrap, 'ensure_default', lambda *a, **k: pytest.fail('override provisioned'))
    with pytest.raises(ConfigurationError, match='not installed'):
        tool.ensure_saucepan_binary()
    assert not target.parent.exists()

@pytest.mark.parametrize('sidecar', [False, True])
def test_actual_init_refuses_raw_manager_and_preserves_existing_state(tmp_path, monkeypatch, sidecar):
    from contextlib import contextmanager
    from typer.testing import CliRunner
    from powerspec.cli import app
    from powerspec import saucepan_tool as tool
    from powerspec.sources import SaucepanSources
    from test_initialization import setup_repo
    project, catalog = setup_repo(tmp_path)
    home = tmp_path / 'home'
    home.mkdir()
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: home))
    monkeypatch.delenv('POWERSPEC_SAUCEPAN', raising=False)
    target = tool.saucepan_executable_path()
    target.parent.mkdir(parents=True)
    target.write_bytes(b'old manager')
    cache = target.with_name('saucepan-check.json')
    cache.write_bytes(b'old cache')
    credential = target.parent.parent / 'private-credentials'
    credential.write_bytes(b'preserved credential fixture')
    if sidecar:
        target.with_suffix('.json').write_bytes(b'unknown sidecar')
    before = {p: p.read_bytes() for p in target.parent.parent.rglob('*') if p.is_file()}
    monkeypatch.setattr(tool, '_probe', lambda *a, **k: '0.10.0')
    monkeypatch.setattr(bootstrap, 'ensure_default', lambda *a, **k: pytest.fail('raw manager installation'))
    builtin = tmp_path / 'catalog'
    (builtin / 'profiles/base.toml').write_text('scope="user"\nskills=["fixture/skills/*"]\n'
        '[[source]]\nid="fixture"\nprovider="git"\norigin="https://example.invalid/repository"\nreference="main"\n')
    @contextmanager
    def resources():
        yield builtin
    monkeypatch.setattr('powerspec.workspace.builtin_catalog_root', resources)
    (project / 'openspec/config.yaml').write_text('schema: spec-driven\n')
    store = SaucepanSources(consumer_path=project / 'openspec/.pspec/config.toml')
    store._write(store._state())
    receipt = store.state_path.read_bytes()
    config = store.consumer_path.read_bytes()
    monkeypatch.chdir(project)
    result = CliRunner().invoke(app, ['init'])
    assert result.exit_code == 1 and 'migration' in result.stderr
    assert hashlib.sha256(target.read_bytes()).hexdigest() in result.stderr
    assert {p: p.read_bytes() for p in target.parent.parent.rglob('*') if p.is_file()} == before
    assert store.state_path.read_bytes() == receipt
    assert store.consumer_path.read_bytes() == config
    assert not list(home.glob('.powerspec-saucepan-backup-*'))

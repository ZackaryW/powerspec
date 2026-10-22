"""Delegate first setup to a verified official installer outside the store."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from uuid import uuid4

from .catalog import ConfigurationError
from .saucepan_provider import PROVIDER, Provider, SetupOutcome
from .progress import stage

MANUAL_SETUP = 'https://github.com/ZackaryW/saucepan/blob/v0.11.0/docs/managed-setup.md'


class SetupFailure(ConfigurationError):
    """Retain the exact provider receipt for callers inspecting failed setup."""
    def __init__(self, message, *, root, operation, outcome=None):
        self.root, self.operation, self.outcome = root, operation, outcome
        receipt = f'; receipt={outcome.model_dump_json()}' if outcome is not None else ''
        super().__init__(f'{message}; root={root}; operation={operation}{receipt}; '
                         f'inspect/recover this provider operation before rerunning init. Official setup: {MANUAL_SETUP}')


def _progress(value):
    if value:
        print(value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value,
              end='' if value.endswith(b'\n' if isinstance(value, bytes) else '\n') else '\n', file=sys.stderr)


def run_installer(argv, target, operation, *, timeout=600):
    """One literal invocation; noncomplete receipts are not transport errors."""
    root = target.parent.parent
    print(f'Saucepan setup: root={root}; operation={operation}', file=sys.stderr)
    try:
        process = subprocess.run(argv, cwd=Path(argv[0]).parent if Path(argv[0]).is_absolute() else Path.cwd(),
            capture_output=True, text=True, encoding='utf-8', errors='replace', shell=False,
            timeout=timeout, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired as error:
        _progress(error.stderr)
        raise SetupFailure('Saucepan setup timed out; mutation may have committed (response lost)',
                           root=root, operation=operation) from error
    except OSError as error:
        raise SetupFailure(f'cannot launch official installer: {error}', root=root, operation=operation) from error
    _progress(process.stderr)
    try:
        result = SetupOutcome.model_validate_json(process.stdout)
        result.check_target(target)
        if result.operation != operation:
            raise ValueError('setup operation mismatch')
        if process.returncode != (0 if result.status == 'complete' else 2):
            raise ValueError('setup exit/result mismatch')
    except ValueError as error:
        raise SetupFailure(f'Saucepan setup response unavailable or invalid (exit {process.returncode}); '
                           'mutation may have committed; no automatic retry', root=root, operation=operation) from error
    if result.status != 'complete':
        raise SetupFailure(f'Saucepan setup {result.status}', root=root, operation=operation, outcome=result)
    return result


def _download(url, destination, expected):
    limit = 1024 * 1024
    with urllib.request.urlopen(url, timeout=30) as response:
        content = response.read(limit + 1)
    if len(content) > limit or hashlib.sha256(content).hexdigest() != expected:
        raise ConfigurationError('official Saucepan installer checksum mismatch or size limit exceeded')
    destination.write_bytes(content)


def migration_record(target: Path) -> Path:
    """Caller attempt evidence outside the provider store, never provider metadata."""
    identity = os.path.normcase(str(target.parent.parent.resolve()))
    return Path.home() / '.powerspec/saucepan-setup' / (hashlib.sha256(identity.encode()).hexdigest() + '.json')


def ensure_default(target: Path, *, provider: Provider = PROVIDER, expected_sha256: str | None = None) -> Path:
    """Provider owns all root validation, initialization, receipts and publication."""
    from .saucepan_tool import inspect_saucepan_binary

    record = migration_record(target)
    if record.exists():
        # Ready launchers are accepted before this boundary. Any other state
        # needs explicit provider recovery, not another invocation with force.
        try:
            previous = json.loads(record.read_text(encoding='utf-8'))
            operation = previous['operation']
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise ConfigurationError(f'unreadable migration attempt {record}; inspect provider setup-status externally') from error
        raise SetupFailure(f'previous migration attempt retained at {record}; inspect setup-status with an external '
                           'setup-capable manager if the launcher is unavailable; no automatic retry',
                           root=target.parent.parent, operation=operation)
    name, url, digest = provider.installer()
    shell = shutil.which('powershell.exe' if name == 'install.ps1' else 'sh')
    if shell is None:
        raise ConfigurationError(f'missing official installer prerequisite: {name}; follow {MANUAL_SETUP}')
    operation = str(uuid4())
    with tempfile.TemporaryDirectory(prefix='powerspec-saucepan-') as directory:
        stage_directory = Path(directory).resolve()
        root = target.parent.parent.resolve()
        if stage_directory.is_relative_to(root):
            raise ConfigurationError('official installer staging must be outside the Saucepan store')
        installer = stage_directory / name
        _download(url, installer, digest)
        if name == 'install.ps1':
            argv = [shell, '-NoLogo', '-NoProfile', '-NonInteractive', '-File', str(installer),
                    '-Version', provider.tag, '-Root', str(root), '-Operation', operation]
            if provider.fixture_api is not None:
                argv += ['-TestReleaseBase', provider.release_base, '-TestGithubApi', provider.fixture_api]
        else:
            argv = [shell, str(installer), '--version', provider.tag, '--root', str(root), '--operation', operation]
            if provider.fixture_api is not None:
                argv += ['--test-release-base', provider.release_base, '--test-github-api', provider.fixture_api]
        if expected_sha256 is not None:
            argv += (['-MigrateUnmanaged', '-ExpectedSha256', expected_sha256] if name == 'install.ps1'
                     else ['--migrate-unmanaged', '--expected-sha256', expected_sha256])
            record.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation also prevents concurrent migrations. Never
            # erase this evidence after timeout, response loss or success.
            try:
                with record.open('x', encoding='utf-8') as stream:
                    json.dump(dict(root=str(root), operation=operation, tag=provider.tag,
                                   expected_sha256=expected_sha256), stream)
                    stream.flush()
                    os.fsync(stream.fileno())
            except FileExistsError as error:
                raise ConfigurationError(f'migration already reserved; inspect {record} before recovery') from error
        label = 'Migrating Saucepan manager' if expected_sha256 else 'Installing Saucepan manager'
        with stage(label) as task:
            if expected_sha256:
                print(f'Saucepan migration: root={root}; SHA256={expected_sha256}; operation={operation}', file=sys.stderr)
            result = run_installer(argv, target, operation)
            task.result('done', f'operation={operation}; backups={result.backup_paths}')
        try:
            return inspect_saucepan_binary(Path(result.launcher_path))
        except ConfigurationError as error:
            raise SetupFailure(f'setup completed but reinspection failed: {error}', root=root,
                               operation=operation, outcome=result) from error

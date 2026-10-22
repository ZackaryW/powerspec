"""Delegate first setup to a verified official installer outside the store."""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from uuid import uuid4

from .catalog import ConfigurationError
from .saucepan_provider import PROVIDER, Provider, SetupOutcome

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


def ensure_default(target: Path, *, provider: Provider = PROVIDER) -> Path:
    """Provider owns all root validation, initialization, receipts and publication."""
    from .saucepan_tool import inspect_saucepan_binary

    name, url, digest = provider.installer()
    shell = shutil.which('powershell.exe' if name == 'install.ps1' else 'sh')
    if shell is None:
        raise ConfigurationError(f'missing official installer prerequisite: {name}; follow {MANUAL_SETUP}')
    operation = str(uuid4())
    with tempfile.TemporaryDirectory(prefix='powerspec-saucepan-') as directory:
        stage = Path(directory).resolve()
        root = target.parent.parent.resolve()
        if stage.is_relative_to(root):
            raise ConfigurationError('official installer staging must be outside the Saucepan store')
        installer = stage / name
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
        result = run_installer(argv, target, operation)
        try:
            return inspect_saucepan_binary(Path(result.launcher_path))
        except ConfigurationError as error:
            raise SetupFailure(f'setup completed but reinspection failed: {error}', root=root,
                               operation=operation, outcome=result) from error

"""Inspect provider ownership; provision only an absent default installation."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import shlex
import subprocess
from time import monotonic

from .catalog import ConfigurationError, MetadataUnavailable
from .saucepan_provider import PROVIDER, SetupStatus, same_path
from .utils.inspection import inspect_executable

SAUCEPAN_CLI_LINES = {(0, 10), (0, 11)}


def saucepan_executable_path() -> Path:
    override = os.environ.get('POWERSPEC_SAUCEPAN')
    return Path(override).expanduser().absolute() if override else Path.home() / '.saucepan/bin' / ('saucepan.exe' if os.name == 'nt' else 'saucepan')


def standalone(target: Path) -> bool:
    return bool(os.environ.get('POWERSPEC_SAUCEPAN')) or not same_path(
        target, Path.home() / '.saucepan/bin' / ('saucepan.exe' if os.name == 'nt' else 'saucepan'))


def _version(value):
    match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)(?:[+-][0-9A-Za-z.-]+)?', value)
    return tuple(map(int, match.groups())) if match else None


def _compatible(value: str) -> bool:
    version = _version(value)
    return version is not None and version[:2] in SAUCEPAN_CLI_LINES


def _saucepan_version(text: str) -> str:
    output = text.strip()
    if not output.startswith('saucepan '):
        raise ValueError('Saucepan --version returned an unsupported response')
    return output.removeprefix('saucepan ')


def inspection_remaining(deadline: float) -> float:
    remaining = deadline - monotonic()
    if remaining <= 0:
        raise MetadataUnavailable('skill metadata inspection budget exhausted')
    return remaining


def _inspect(path: Path, *arguments: str, parse=None, deadline=None):
    return inspect_executable([str(path), *arguments], cwd=path.parent,
        timeout=15 if deadline is None else inspection_remaining(deadline), parse_version=parse,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))


def _probe(path: Path, *, deadline=None) -> str:
    result = _inspect(path, '--version', parse=_saucepan_version, deadline=deadline)
    if not result.ok:
        raise ValueError(f'Saucepan version inspection failed: {result.kind}')
    return result.version or ''


def _validate(path: Path, _tag: str, *, deadline=None) -> None:
    result = _inspect(path, '--help', deadline=deadline)
    required = {'register-application', 'register-source', 'prepare-group', 'pin', 'inspect', 'profile'}
    if not result.ok or not required.issubset(set(result.stdout.split())):
        raise ValueError('Saucepan command surface is incompatible')


def migration_guidance(target):
    with target.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    root = str(target.parent.parent)
    if os.name == 'nt':
        quoted_root = "'" + root.replace("'", "''") + "'"
        command = (f'powershell.exe -NoProfile -File <verified-install.ps1> -Version {PROVIDER.tag} '
                   f'-Root {quoted_root} -Operation <UUID> -MigrateUnmanaged -ExpectedSha256 {digest}')
    else:
        command = (f'sh <verified-install.sh> --version {PROVIDER.tag} --root {shlex.quote(root)} '
                   f'--operation <UUID> --migrate-unmanaged --expected-sha256 {digest}')
    return (f'Saucepan unmanaged manager needs explicit verified migration; observed SHA256 {digest}. '
            f'Preserve the root and run the verified official installer externally: {command}. '
            'Binary-only/uninitialized roots require manual preservation or a separate root; '
            'do not rerun init to authorize migration. See docs/remote-sources.md#retention-and-recovery')


def inspect_managed_status(target: Path, *, deadline=None) -> SetupStatus:
    result = _inspect(target, '--root', str(target.parent.parent), 'setup-status', deadline=deadline)
    if not result.ok:
        raise ValueError(f'Saucepan setup-status failed: {result.kind}; inspect the root with an external setup-capable manager')
    status = SetupStatus.model_validate_json(result.stdout)
    status.check_target(target)
    return status


def require_ready(target, status, version):
    if status.state == 'unmanaged':
        raise ValueError(migration_guidance(target))
    if status.state != 'ready':
        raise ValueError(f'Saucepan managed state {status.state}; root={status.root}; operation={status.operation}; '
                         f'{"; ".join(status.diagnostics)}; inspect/recover the provider operation before rerunning init')
    if _version(status.installed_version) != _version(version):
        raise ValueError('Saucepan installed version differs from its managed status')
    if not _compatible(version):
        raise ValueError(f'unsupported Saucepan version {version}; explicitly run Saucepan --root "{status.root}" '
                         f'self-update {status.app} {status.claim} --tag {PROVIDER.tag} --operation <UUID>')


def inspect_saucepan_binary(destination: Path | None = None, *, deadline=None) -> Path:
    target = Path(destination).absolute() if destination is not None else saucepan_executable_path()
    if not target.is_file():
        raise MetadataUnavailable(f'Saucepan is not installed at {target}; use official setup/recovery before source access')
    deadline = monotonic() + 15 if deadline is None else deadline
    try:
        version = _probe(target, deadline=deadline)
        if standalone(target):
            if not _compatible(version):
                raise ValueError(f'unsupported Saucepan version {version}; select a compatible standalone executable')
            _validate(target, version, deadline=deadline)
        else:
            parsed = _version(version)
            if parsed is None or parsed < (0, 11, 0):
                raise ValueError(migration_guidance(target))
            status = inspect_managed_status(target, deadline=deadline)
            require_ready(target, status, version)
        return target
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise MetadataUnavailable(f'cannot use existing Saucepan: {error}') from error


def ensure_saucepan_binary(destination: Path | None = None) -> Path:
    target = Path(destination).absolute() if destination is not None else saucepan_executable_path()
    if standalone(target) or target.exists() or target.is_symlink():
        return inspect_saucepan_binary(target)
    from .saucepan_bootstrap import ensure_default
    try:
        return ensure_default(target)
    except ConfigurationError:
        raise
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise ConfigurationError(f'cannot set up Saucepan: {error}') from error


__all__ = ['ensure_saucepan_binary', 'inspect_saucepan_binary']

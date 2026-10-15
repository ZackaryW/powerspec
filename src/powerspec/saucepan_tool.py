"""Keep the Saucepan SDK's shared executable installed and compatible."""
from __future__ import annotations

import subprocess
import os
import shutil
import tempfile
import urllib.request
import zipfile
from time import monotonic
from datetime import timedelta
from pathlib import Path

from zuu.case16 import GitHubReleaseResolver, ReleaseAsset, parse_version, select_rust_asset
from zuu.case17 import FileCheckStateStore, ManagedReleaseBinary, ManagedReleaseBinaryError

from .catalog import ConfigurationError, MetadataUnavailable
from .utils.inspection import inspect_executable


SAUCEPAN_CLI_LINES = {(0, 9)}


def saucepan_executable_path() -> Path:
    """Resolve the app's explicit override or shared manager destination."""
    override = os.environ.get('POWERSPEC_SAUCEPAN')
    return Path(override).expanduser() if override else Path.home() / '.saucepan/bin' / ('saucepan.exe' if os.name == 'nt' else 'saucepan')


def _select_manager_zip(assets, system, machine):
    candidates = {}
    for asset in assets:
        if asset.name.startswith('saucepan-') and asset.name.endswith('.zip'):
            name = asset.name[:-4]
            if system.lower() == 'windows':
                name += '.exe'
            candidates[name] = asset
    selected = select_rust_asset(tuple(ReleaseAsset(name, item.url) for name, item in candidates.items()), system, machine)
    return candidates[selected.name]


def _download_manager(url: str, destination: Path) -> None:
    """Read only the release's exact manager member into Zuu's staging file."""
    limit = 256 * 1024 * 1024
    with tempfile.TemporaryFile() as archive:
        with urllib.request.urlopen(url, timeout=30) as response:
            remaining = limit
            while block := response.read(min(1024 * 1024, remaining + 1)):
                remaining -= len(block)
                if remaining < 0:
                    raise ValueError('Saucepan release archive exceeds size limit')
                archive.write(block)
        archive.seek(0)
        with zipfile.ZipFile(archive) as bundle:
            name = 'saucepan.exe' if os.name == 'nt' else 'saucepan'
            members = [item for item in bundle.infolist() if item.filename == name]
            if len(members) != 1 or members[0].is_dir() or members[0].file_size > limit:
                raise ValueError('release must contain one bounded manager executable')
            with bundle.open(members[0]) as source, destination.open('wb') as target:
                shutil.copyfileobj(source, target)


def _compatible(value: str) -> bool:
    parsed = parse_version(value)
    if parsed is None:
        return False
    core = parsed[0] + (0,)
    return core[:2] in SAUCEPAN_CLI_LINES


def _saucepan_version(text: str) -> str:
    output = text.strip()
    prefix = "saucepan "
    if not output.startswith(prefix):
        raise ValueError("Saucepan --version returned an unsupported response")
    return output.removeprefix(prefix)


def inspection_remaining(deadline: float) -> float:
    remaining = deadline - monotonic()
    if remaining <= 0:
        raise MetadataUnavailable('skill metadata inspection budget exhausted')
    return remaining


def _inspect(path: Path, *arguments: str, parse=None, deadline=None):
    return inspect_executable(
        [str(path), *arguments],
        cwd=path.parent,
        timeout=15 if deadline is None else inspection_remaining(deadline),
        parse_version=parse,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _probe(path: Path, *, deadline=None) -> str:
    result = _inspect(path, "--version", parse=_saucepan_version, deadline=deadline)
    if not result.ok:
        raise ValueError(f"Saucepan version inspection failed: {result.kind}")
    return result.version or ""


def _validate(path: Path, _tag: str, *, deadline=None) -> None:
    result = _inspect(path, "--help", deadline=deadline)
    if not result.ok:
        raise ValueError(f"Saucepan validation failed: {result.kind}")
    required = {'register-application', 'register-source', 'prepare-group', 'pin', 'inspect'}
    if not required.issubset(set(result.stdout.split())):
        raise ValueError('Saucepan command surface is incompatible')


def _managed_saucepan(destination: Path) -> ManagedReleaseBinary:
    resolver = GitHubReleaseResolver(
        "ZackaryW",
        "saucepan",
        candidate_filter=lambda candidate: _compatible(candidate.tag),
        asset_selector=_select_manager_zip,
    )
    return ManagedReleaseBinary(
        resolver=resolver,
        destination=destination,
        probe=_probe,
        is_compatible=_compatible,
        validator=_validate,
        state_store=FileCheckStateStore(destination.with_name("saucepan-check.json")),
        max_age=timedelta(hours=24),
        policy_id="saucepan-cli-0.9-zip-v1",
    )


def ensure_saucepan_binary(destination: Path | None = None) -> Path:
    """Return a usable shared Saucepan binary, installing or upgrading via Zuu."""
    target = Path(destination) if destination is not None else saucepan_executable_path()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        return _managed_saucepan(target).ensure(downloader=_download_manager).destination
    except (ManagedReleaseBinaryError, OSError, ValueError) as error:
        raise ConfigurationError(f"cannot install or update Saucepan: {error}") from error


def inspect_saucepan_binary(destination: Path | None = None, *, deadline=None) -> Path:
    """Return an existing compatible binary without creating or updating it."""
    target = Path(destination) if destination is not None else saucepan_executable_path()
    if not target.is_file():
        raise MetadataUnavailable(f"Saucepan is not installed at {target}")
    try:
        options = {} if deadline is None else {'deadline': deadline}
        version = _probe(target, **options)
        if not _compatible(version):
            raise ValueError(f"unsupported Saucepan version {version}")
        _validate(target, version, **options)
        return target
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise MetadataUnavailable(f"cannot use existing Saucepan: {error}") from error


__all__ = ["ensure_saucepan_binary", "inspect_saucepan_binary"]

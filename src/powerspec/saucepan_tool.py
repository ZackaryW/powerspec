"""Keep the Saucepan SDK's shared executable installed and compatible."""
from __future__ import annotations

import subprocess
from datetime import timedelta
from pathlib import Path

from saucepan_sdk.client import shared_executable_path
from zuu.case16 import GitHubReleaseResolver, parse_version
from zuu.case17 import FileCheckStateStore, ManagedReleaseBinary, ManagedReleaseBinaryError

from .catalog import ConfigurationError
from .utils.inspection import inspect_executable


SAUCEPAN_CLI_LINES = {(0, 5), (0, 6)}


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


def _inspect(path: Path, *arguments: str, parse=None):
    return inspect_executable(
        [str(path), *arguments],
        cwd=path.parent,
        timeout=15,
        parse_version=parse,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _probe(path: Path) -> str:
    result = _inspect(path, "--version", parse=_saucepan_version)
    if not result.ok:
        raise ValueError(f"Saucepan version inspection failed: {result.kind}")
    return result.version or ""


def _validate(path: Path, _tag: str) -> None:
    result = _inspect(path, "--help")
    if not result.ok:
        raise ValueError(f"Saucepan validation failed: {result.kind}")


def _managed_saucepan(destination: Path) -> ManagedReleaseBinary:
    resolver = GitHubReleaseResolver(
        "ZackaryW",
        "saucepan",
        candidate_filter=lambda candidate: _compatible(candidate.tag),
    )
    return ManagedReleaseBinary(
        resolver=resolver,
        destination=destination,
        probe=_probe,
        is_compatible=_compatible,
        validator=_validate,
        state_store=FileCheckStateStore(destination.with_name("saucepan-check.json")),
        max_age=timedelta(hours=24),
        policy_id="saucepan-cli-0.5-0.6-v1",
    )


def ensure_saucepan_binary(destination: Path | None = None) -> Path:
    """Return a usable shared Saucepan binary, installing or upgrading via Zuu."""
    target = Path(destination) if destination is not None else shared_executable_path()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        return _managed_saucepan(target).ensure().destination
    except (ManagedReleaseBinaryError, OSError, ValueError) as error:
        raise ConfigurationError(f"cannot install or update Saucepan: {error}") from error


def inspect_saucepan_binary(destination: Path | None = None) -> Path:
    """Return an existing compatible binary without creating or updating it."""
    target = Path(destination) if destination is not None else shared_executable_path()
    if not target.is_file():
        raise ConfigurationError(f"Saucepan is not installed at {target}")
    try:
        version = _probe(target)
        if not _compatible(version):
            raise ValueError(f"unsupported Saucepan version {version}")
        _validate(target, version)
        return target
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise ConfigurationError(f"cannot use existing Saucepan: {error}") from error


__all__ = ["ensure_saucepan_binary", "inspect_saucepan_binary"]

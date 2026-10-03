"""Keep the Saucepan SDK's shared executable installed and compatible."""
from __future__ import annotations

import subprocess
from datetime import timedelta
from importlib.metadata import version
from pathlib import Path

from saucepan_sdk.client import shared_executable_path
from zuu.case16 import GitHubReleaseResolver, parse_version
from zuu.case17 import FileCheckStateStore, ManagedReleaseBinary, ManagedReleaseBinaryError

from .catalog import ConfigurationError


SAUCEPAN_SDK_VERSION = version("saucepan-sdk")


def _version_line(value: str) -> tuple[int, int]:
    parsed = parse_version(value)
    if parsed is None:
        raise ConfigurationError(f"unsupported saucepan-sdk version: {value!r}")
    core = parsed[0] + (0,)
    return core[0], core[1]


SAUCEPAN_SDK_LINE = _version_line(SAUCEPAN_SDK_VERSION)


def _compatible(value: str) -> bool:
    parsed = parse_version(value)
    if parsed is None:
        return False
    core = parsed[0] + (0,)
    return core[:2] == SAUCEPAN_SDK_LINE


def _probe(path: Path) -> str:
    completed = subprocess.run(
        [str(path), "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    output = completed.stdout.strip()
    prefix = "saucepan "
    if not output.startswith(prefix):
        raise ValueError("Saucepan --version returned an unsupported response")
    return output.removeprefix(prefix)


def _validate(path: Path, _tag: str) -> None:
    subprocess.run(
        [str(path), "--help"],
        check=True,
        capture_output=True,
        timeout=15,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _managed_saucepan(destination: Path) -> ManagedReleaseBinary:
    line = ".".join(map(str, SAUCEPAN_SDK_LINE))
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
        policy_id=f"saucepan-sdk-{line}-v1",
    )


def ensure_saucepan_binary(destination: Path | None = None) -> Path:
    """Return a usable shared Saucepan binary, installing or upgrading via Zuu."""
    target = Path(destination) if destination is not None else shared_executable_path()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        return _managed_saucepan(target).ensure().destination
    except (ManagedReleaseBinaryError, OSError, ValueError) as error:
        raise ConfigurationError(f"cannot install or update Saucepan: {error}") from error


__all__ = ["ensure_saucepan_binary"]

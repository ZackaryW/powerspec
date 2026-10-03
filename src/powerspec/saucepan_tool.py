"""Keep the Saucepan SDK's shared executable installed and compatible."""
from __future__ import annotations

import subprocess
from datetime import timedelta
from pathlib import Path

from saucepan_sdk.client import shared_executable_path
from zuu.case16 import GitHubReleaseResolver, parse_version
from zuu.case17 import FileCheckStateStore, ManagedReleaseBinary, ManagedReleaseBinaryError

from .catalog import ConfigurationError


SAUCEPAN_CLI_LINES = {(0, 5), (0, 6)}


def _compatible(value: str) -> bool:
    parsed = parse_version(value)
    if parsed is None:
        return False
    core = parsed[0] + (0,)
    return core[:2] in SAUCEPAN_CLI_LINES


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


__all__ = ["ensure_saucepan_binary"]

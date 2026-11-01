"""Observe Powerspec prerequisites without installing or repairing them."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .consumer import discover_consumer
from .milkpan_binary import MILKPAN, SUPPORTED_LINES, default_home, link_executable, manager_state, standalone
from .milkpan_client import Milkpan
from .utils.inspection import ExecutableResult, inspect_executable, semantic_version


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class DoctorResult:
    checks: tuple[DoctorCheck, ...]

    @property
    def ok(self) -> bool:
        return all(item.status != "failed" for item in self.checks)


def _check(name: str, result: ExecutableResult, *, minimum=None, compatible=None) -> DoctorCheck:
    if not result.ok:
        detail = {
            "missing": "executable is missing",
            "timeout": "version check timed out",
            "exit": f"version check exited {result.returncode}",
            "version": "version output is unsupported",
            "launch": result.stderr or "executable could not be launched",
        }.get(result.kind, result.kind)
        return DoctorCheck(name, "failed", detail)
    if minimum is not None:
        parts = tuple(int(part) for part in (result.version or "0").split("."))
        if parts < minimum:
            return DoctorCheck(name, "failed", f"{result.version} is older than {'.'.join(map(str, minimum))}")
    if compatible is not None and not compatible(result.version or ""):
        return DoctorCheck(name, "failed", f"unsupported version {result.version or 'unknown'}")
    return DoctorCheck(name, "ok", result.version or result.executable or "available")


def _compatible(version: str) -> bool:
    try:
        major, minor, *_ = version.split(".")
        return (int(major), int(minor)) in SUPPORTED_LINES
    except ValueError:
        return False


def managed_state(home: Path) -> str:
    """`current`, `behind` or `absent` for the managed link's release lease (read-only)."""
    client = Milkpan(link_executable(home), home, timeout=15, env=MILKPAN.client_env())
    return manager_state(client, MILKPAN, MILKPAN.target())


def doctor_consumer(cwd: Path, *, milkpan_path: Path | None = None, milkpan_home: Path | None = None,
                    agent: str | None = None) -> DoctorResult:
    """Return named prerequisite observations without changing the environment."""
    if agent is not None:
        from .hooks import callback_for
        callback_for(agent, 'sessionStart')
    cwd = Path(cwd).resolve(strict=True)
    try:
        consumer = discover_consumer(cwd, runtime=False)
    except (OSError, ValueError) as error:
        consumer_check = DoctorCheck("consumer", "failed", str(error))
        root = cwd
    else:
        consumer_check = (
            DoctorCheck("consumer", "ok", str(consumer.git_root))
            if consumer is not None
            else DoctorCheck("consumer", "failed", "no owning openspec/.pspec/config.toml")
        )
        root = consumer.git_root if consumer is not None else cwd
    git = inspect_executable(["git", "--version"], cwd=root, timeout=15, parse_version=semantic_version)
    openspec = inspect_executable(["openspec", "--version"], cwd=root, timeout=15, parse_version=semantic_version)
    home = milkpan_home or default_home()
    override = milkpan_path or standalone()
    target = override or link_executable(home)
    milkpan = inspect_executable([str(target), "--version"], cwd=root, timeout=15, parse_version=semantic_version)
    milkpan_check = _check("milkpan", milkpan, compatible=_compatible)
    if milkpan_check.status == "ok":
        milkpan_check = DoctorCheck("milkpan", "ok", f"executable compatible ({milkpan.version})")
    if override is not None:
        installation = DoctorCheck("milkpan-installation", "warning",
            "explicit standalone executable; managed link not required or inspected")
    elif not milkpan.ok:
        installation = DoctorCheck("milkpan-installation", "warning",
            "managed milkpan not prepared; init or upgrade prepares it")
    else:
        state = managed_state(home)
        installation = {
            "current": DoctorCheck("milkpan-installation", "ok", f"managed link current ({MILKPAN.tag})"),
            "behind": DoctorCheck("milkpan-installation", "warning",
                f"managed link behind the pinned {MILKPAN.tag}; the next init or upgrade switches it"),
        }.get(state, DoctorCheck("milkpan-installation", "failed",
            "managed link has no release lease; rerun init"))
    checks = (
        consumer_check,
        _check("git", git),
        _check("openspec", openspec, minimum=(1, 14, 3)),
        milkpan_check,
        installation,
        DoctorCheck('milkpan-sources', 'warning', 'selected-source readiness not checked'),
    )
    if agent is None:
        return DoctorResult((*checks, DoctorCheck('guidance', 'warning',
            'delivery not inspected; use doctor --agent codex or --agent claude')))
    from .guidance_doctor import inspect_guidance
    return DoctorResult((*checks, *inspect_guidance(cwd, agent, inspect=inspect_executable)))

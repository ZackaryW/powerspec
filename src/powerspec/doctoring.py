"""Observe Powerspec prerequisites without installing or repairing them."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .consumer import discover_consumer
from .saucepan_tool import _compatible, saucepan_executable_path
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


def doctor_consumer(cwd: Path, *, saucepan_path: Path | None = None, agent: str | None = None) -> DoctorResult:
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
    saucepan = inspect_executable(
        [str(saucepan_path or saucepan_executable_path()), "--version"],
        cwd=root,
        timeout=15,
        parse_version=semantic_version,
    )
    saucepan_check = _check("saucepan", saucepan, compatible=_compatible)
    if saucepan_check.status == 'ok':
        saucepan_check = DoctorCheck('saucepan', 'ok',
            f'executable compatible ({saucepan.version}); store/source readiness not checked')
    checks = (
        consumer_check,
        _check("git", git),
        _check("openspec", openspec, minimum=(1, 13, 2)),
        saucepan_check,
    )
    if agent is None:
        return DoctorResult((*checks, DoctorCheck('guidance', 'warning',
            'delivery not inspected; use doctor --agent codex or --agent claude')))
    from .guidance_doctor import inspect_guidance
    return DoctorResult((*checks, *inspect_guidance(cwd, agent, inspect=inspect_executable)))

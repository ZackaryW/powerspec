"""Observe Powerspec prerequisites without installing or repairing them."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import monotonic

from .consumer import discover_consumer
from .saucepan_tool import _compatible, saucepan_executable_path
from . import saucepan_tool
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
    target = saucepan_path or saucepan_executable_path()
    deadline = monotonic() + 15
    saucepan = inspect_executable(
        [str(target), "--version"],
        cwd=root,
        timeout=15,
        parse_version=semantic_version,
    )
    saucepan_check = _check("saucepan", saucepan, compatible=_compatible)
    if saucepan_check.status == 'ok':
        saucepan_check = DoctorCheck('saucepan', 'ok',
            f'executable compatible ({saucepan.version})')
    if saucepan_tool.standalone(target):
        installation = DoctorCheck('saucepan-installation', 'warning',
            'explicit standalone executable; managed ownership not required or inspected')
    elif not saucepan.ok:
        installation = DoctorCheck('saucepan-installation', 'failed',
            'absent or uninspectable managed installation; use official setup/recovery')
    elif (saucepan_tool._version(saucepan.version or '') or (0,)) < (0, 11, 0):
        try:
            detail = saucepan_tool.migration_guidance(target)
        except OSError:
            detail = 'unmanaged old manager; explicit verified migration required'
        installation = DoctorCheck('saucepan-installation', 'failed', detail)
    else:
        try:
            status = saucepan_tool.inspect_managed_status(target, deadline=deadline)
            saucepan_tool.require_ready(target, status, saucepan.version)
        except (OSError, ValueError) as error:
            installation = DoctorCheck('saucepan-installation', 'failed', str(error))
        else:
            installation = DoctorCheck('saucepan-installation', 'ok', f'managed state ready; root={status.root}')
    checks = (
        consumer_check,
        _check("git", git),
        _check("openspec", openspec, minimum=(1, 13, 2)),
        saucepan_check,
        installation,
        DoctorCheck('saucepan-sources', 'warning', 'selected-source readiness not checked'),
    )
    if agent is None:
        return DoctorResult((*checks, DoctorCheck('guidance', 'warning',
            'delivery not inspected; use doctor --agent codex or --agent claude')))
    from .guidance_doctor import inspect_guidance
    return DoctorResult((*checks, *inspect_guidance(cwd, agent, inspect=inspect_executable)))

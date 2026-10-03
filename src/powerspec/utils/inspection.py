"""Inspect caller-selected executables without installing or repairing them."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess


@dataclass(frozen=True)
class ExecutableResult:
    kind: str
    executable: str | None = None
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    version: str | None = None

    @property
    def ok(self) -> bool:
        return self.kind == "ok"


def inspect_executable(
    argv: Sequence[str],
    *,
    cwd: Path,
    timeout: float,
    parse_version: Callable[[str], str] | None = None,
) -> ExecutableResult:
    """Run literal argv with a time bound and return a categorized observation."""
    if isinstance(argv, (str, bytes)) or not argv or any(not isinstance(x, str) or not x for x in argv):
        raise ValueError("argv must be a nonempty sequence of nonempty strings")
    executable = shutil.which(argv[0])
    if executable is None:
        return ExecutableResult("missing")
    command = [executable, *argv[1:]]
    try:
        process = subprocess.run(
            command,
            cwd=Path(cwd),
            timeout=timeout,
            capture_output=True,
            text=True,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return ExecutableResult("timeout", executable=executable)
    except (OSError, ValueError) as error:
        return ExecutableResult("launch", executable=executable, stderr=str(error))
    if process.returncode:
        return ExecutableResult(
            "exit", executable, process.returncode, process.stdout, process.stderr
        )
    version = None
    if parse_version is not None:
        try:
            version = parse_version(process.stdout)
        except (TypeError, ValueError) as error:
            return ExecutableResult(
                "version", executable, process.returncode, process.stdout, str(error)
            )
    return ExecutableResult(
        "ok", executable, process.returncode, process.stdout, process.stderr, version
    )

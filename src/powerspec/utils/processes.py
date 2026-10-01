"""Run caller-selected commands and distinguish JSON data from process failures."""
from collections.abc import Mapping, Sequence
import json
import math
from pathlib import Path
import subprocess


class ProcessJSONError(ValueError):
    """A process-to-object failure with a stable category and optional exit code."""
    def __init__(self, kind: str, message: str, *, returncode: int | None = None):
        super().__init__(message)
        self.kind = kind
        self.returncode = returncode


def run_json_object(argv: Sequence[str], *, cwd: Path, env: Mapping[str, str], timeout: float) -> dict[str, object]:
    """Execute literal argv without a shell, require exit zero and object JSON.

    No retries, output printing, environment mutation, or effect rollback.
    """
    if (isinstance(argv, (str, bytes)) or not isinstance(argv, Sequence) or not argv
            or any(not isinstance(arg, str) or "\x00" in arg for arg in argv) or not argv[0]):
        raise ProcessJSONError("arguments", "argv must be a nonempty sequence of string arguments")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ProcessJSONError("arguments", "timeout must be a finite positive number")
    try:
        process = subprocess.run(list(argv), cwd=cwd, env=dict(env), timeout=timeout,
                                 shell=False, capture_output=True, text=True, encoding="utf-8")
    except subprocess.TimeoutExpired as error:
        raise ProcessJSONError("timeout", f"command timed out after {timeout}s: {argv[0]}") from error
    except UnicodeError as error:
        raise ProcessJSONError("json", f"command output is not UTF-8: {argv[0]}") from error
    except (OSError, ValueError) as error:
        raise ProcessJSONError("launch", f"cannot launch command {argv[0]}: {error}") from error
    if process.returncode:
        raise ProcessJSONError("exit", f"command {argv[0]} exited {process.returncode}", returncode=process.returncode)
    try:
        value = json.loads(process.stdout)
    except ValueError as error:
        raise ProcessJSONError("json", f"command did not return valid JSON: {argv[0]}") from error
    if not isinstance(value, dict):
        raise ProcessJSONError("object", f"command JSON must be an object: {argv[0]}")
    return value

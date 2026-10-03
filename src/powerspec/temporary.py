"""Validated, atomic cleanup of one consumer's gitignored runtime values."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tempfile

from pydantic import ValidationError
import tomlkit

from .catalog import ConfigurationError
from .consumer import discover_consumer
from .models import Variables


@dataclass(frozen=True)
class FlushResult:
    path: Path
    updated: bool


def _parse(original: bytes, path: Path):
    try:
        document = tomlkit.parse(original.decode("utf-8-sig"))
        values = Variables.model_validate(document.unwrap())
        return document, values
    except (UnicodeError, ValueError, ValidationError) as error:
        raise ConfigurationError(f"{path}: invalid temporal state: {error}") from error


def _validate_candidate(candidate: bytes, path: Path) -> None:
    _parse(candidate, path)


def _publish(path: Path, candidate: bytes) -> None:
    temporary = None
    try:
        handle, name = tempfile.mkstemp(prefix=f".{path.name}.pspec-", dir=path.parent)
        temporary = Path(name)
        with os.fdopen(handle, "wb") as stream:
            stream.write(candidate)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    except OSError as error:
        raise ConfigurationError(f"{path}: publication failed: {error}") from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def flush_current(cwd: Path, *, change: str | None = None) -> FlushResult:
    """Clear all temporal values or one direct change layer for the nearest consumer."""
    if change is not None and (not isinstance(change, str) or not change.strip()):
        raise ConfigurationError("change must be an explicit nonempty name")
    consumer = discover_consumer(cwd, runtime=False)
    if consumer is None:
        raise ConfigurationError("no owning openspec/.pspec/config.toml within this Git repository")
    path = consumer.config_path.parent / "current.toml"
    try:
        original = path.read_bytes()
    except FileNotFoundError:
        return FlushResult(path, False)
    except OSError as error:
        raise ConfigurationError(f"{path}: {error}") from error

    document, values = _parse(original, path)
    if change is None:
        if not values.vars and not values.changes:
            return FlushResult(path, False)
        empty = tomlkit.document()
        empty.add("vars", tomlkit.table())
        candidate = tomlkit.dumps(empty).encode("utf-8")
    else:
        changes = document.get("_change")
        if changes is None or change not in changes:
            return FlushResult(path, False)
        del changes[change]
        if not changes:
            del document["_change"]
        candidate = tomlkit.dumps(document).encode("utf-8")

    _validate_candidate(candidate, path)
    if candidate == original:
        return FlushResult(path, False)
    _publish(path, candidate)
    return FlushResult(path, True)

"""Atomically replace file bytes without exposing partial content."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile


class AtomicWriteError(OSError):
    """An atomic file replacement could not be completed."""


def replace_bytes(path: Path, content: bytes) -> bool:
    """Replace *path* atomically and return whether its bytes changed.

    The caller owns parent-directory creation and validation. A staging file is
    created beside the destination so ``os.replace`` stays on one filesystem.
    """
    target = Path(path)
    if not target.parent.is_dir():
        raise AtomicWriteError(f"parent directory does not exist: {target.parent}")
    try:
        existing = target.read_bytes() if target.exists() else None
    except OSError as error:
        raise AtomicWriteError(f"cannot read {target}: {error}") from error
    if existing == content:
        return False

    temporary: Path | None = None
    try:
        handle, name = tempfile.mkstemp(prefix=f".{target.name}.pspec-", dir=target.parent)
        temporary = Path(name)
        with os.fdopen(handle, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        temporary = None
    except OSError as error:
        raise AtomicWriteError(f"cannot replace {target}: {error}") from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return True

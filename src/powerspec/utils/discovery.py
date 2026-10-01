"""Find a nearest file within a caller-supplied filesystem boundary."""

from pathlib import Path
from stat import S_ISDIR, S_ISREG


def find_ancestor_file(start: Path, relative_path: str | Path, *, boundary: Path) -> Path | None:
    """Search inclusively upward; missing files return None, inspection errors propagate.

    Paths are canonicalized to reject symlink escapes. This reads metadata only
    and neither parses files nor changes the process working directory.
    """
    start, boundary = Path(start).resolve(strict=True), Path(boundary).resolve(strict=True)
    relative = Path(relative_path)
    if relative.anchor or relative == Path('.') or '..' in relative.parts:
        raise ValueError("relative_path must name a contained relative file")
    if not start.is_relative_to(boundary):
        raise ValueError("start must be within boundary")
    for directory in (start, boundary):
        if not S_ISDIR(directory.stat().st_mode):
            raise NotADirectoryError(directory)
    current = start
    while True:
        candidate = (current / relative).resolve()
        if not candidate.is_relative_to(boundary):
            raise ValueError(f"candidate escapes boundary: {candidate}")
        try:
            info = candidate.stat()
        except FileNotFoundError:
            pass
        else:
            if S_ISREG(info.st_mode):
                return candidate
        if current == boundary:
            return None
        current = current.parent

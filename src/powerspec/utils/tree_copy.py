"""Snapshot and copy regular directory trees without merging or overwriting."""
from dataclasses import dataclass
import hashlib
from pathlib import Path
import shutil
import stat
import tempfile


class TreeError(ValueError):
    pass


@dataclass(frozen=True)
class TreeSnapshot:
    # Directories, including empty ones, have a null digest.
    entries: tuple[tuple[str, str | None], ...]


def assert_plain_path(path: Path) -> None:
    """Reject links/junctions in every existing path component."""
    for component in (path, *path.parents):
        if component.is_symlink() or component.is_junction():
            raise TreeError(f"Refusing link or junction: {component}")


def snapshot_tree(root: Path) -> TreeSnapshot:
    assert_plain_path(root)
    if not root.is_dir():
        raise TreeError(f"Missing directory: {root}")
    entries = []

    def walk(directory):
        for path in sorted(directory.iterdir()):
            mode = path.lstat().st_mode
            if path.is_symlink() or path.is_junction():
                raise TreeError(f"Refusing link: {path}")
            name = path.relative_to(root).as_posix()
            if stat.S_ISDIR(mode):
                entries.append((name, None))
                walk(path)
            elif stat.S_ISREG(mode):
                with path.open("rb") as stream:
                    entries.append((name, hashlib.file_digest(stream, "sha256").hexdigest()))
            else:
                raise TreeError(f"Refusing special file: {path}")
    walk(root)
    return TreeSnapshot(tuple(sorted(entries)))


def copy_verified_tree(source: Path, destination: Path, snapshot: TreeSnapshot) -> bool:
    """Copy a stable snapshot; identical destinations are no-ops, others conflict.

    Source removal belongs to the caller. Concurrent writers are detected by
    snapshots, but this is not a transaction across source and destination.
    """
    assert_plain_path(source)
    assert_plain_path(destination)
    if snapshot_tree(source) != snapshot:
        raise TreeError(f"Source changed: {source}")
    if destination.exists():
        if snapshot_tree(destination) != snapshot:
            raise TreeError(f"Destination has different content: {destination}")
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".pspec-copy-", dir=destination.parent) as temporary:
        staged = Path(temporary) / "tree"
        # Preserve a raced-in link as a link so verification rejects it instead
        # of following it and copying data outside the source boundary.
        shutil.copytree(source, staged, symlinks=True)
        if snapshot_tree(staged) != snapshot or snapshot_tree(source) != snapshot:
            raise TreeError(f"Source changed during copy: {source}")
        if destination.exists():
            raise TreeError(f"Destination appeared during copy: {destination}")
        staged.rename(destination)
    return True

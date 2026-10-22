"""Read-only eligibility checks for OpenSpec paths in a proposed commit."""

from dataclasses import dataclass
from pathlib import Path

from .utils.git_index import IndexReadError, read_index


@dataclass(frozen=True)
class CommitCheck:
    ok: bool
    repository: Path | None
    forbidden_paths: tuple[str, ...] = ()
    unmerged_paths: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


def _active_change_path(path: str) -> bool:
    parts = path.split('/')
    for position in range(len(parts) - 1):
        if [part.casefold() for part in parts[position:position + 2]] == ['openspec', 'changes']:
            # The archive must be a directory with content, not an entry named
            # archive (for example a symlink or submodule) or archive-draft.
            return not (len(parts) > position + 3 and parts[position + 2] == 'archive')
    return False


def check_commit(cwd: Path) -> CommitCheck:
    """Report the selected index; never stage, repair, archive or commit."""
    try:
        index = read_index(cwd)
    except IndexReadError as error:
        return CommitCheck(False, None, errors=(str(error),))
    forbidden = tuple(sorted({entry.path for entry in index.entries
                              if _active_change_path(entry.path)}))
    unmerged = tuple(sorted({entry.path for entry in index.entries if entry.stage != 0}))
    return CommitCheck(not forbidden and not unmerged, index.root, forbidden, unmerged)

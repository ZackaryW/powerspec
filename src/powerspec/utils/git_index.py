"""Read the selected Git index without application-specific path policy."""

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess


class IndexReadError(ValueError):
    """The selected working repository or index could not be inspected."""


@dataclass(frozen=True)
class IndexEntry:
    path: str
    mode: str
    object_id: str
    stage: int


@dataclass(frozen=True)
class GitIndex:
    root: Path
    entries: tuple[IndexEntry, ...]


def read_index(cwd: Path, *, timeout: float = 15) -> GitIndex:
    """Inspect all entries using the caller's Git repository/index environment."""
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_LITERAL_PATHSPECS='0',
               GIT_GLOB_PATHSPECS='0', GIT_NOGLOB_PATHSPECS='0')

    def run(*args: str) -> bytes:
        try:
            result = subprocess.run(['git', '-c', 'core.fsmonitor=false', *args],
                                    cwd=cwd, env=env, capture_output=True,
                                    timeout=timeout, shell=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise IndexReadError(f'Cannot inspect Git index from {cwd}: {error}') from error
        if result.returncode:
            detail = os.fsdecode(result.stderr).strip()
            raise IndexReadError(f'Cannot inspect Git index from {cwd}: {detail}')
        return result.stdout

    root = Path(os.fsdecode(run('rev-parse', '--show-toplevel')).rstrip('\r\n'))
    # Top-anchored selection includes siblings when invoked below the root, while
    # keeping cwd unchanged for relative GIT_DIR/GIT_INDEX_FILE selection.
    raw = run('ls-files', '--stage', '--full-name', '-z', '--', ':/')
    entries = []
    try:
        if raw and not raw.endswith(b'\0'):
            raise ValueError('missing record terminator')
        for record in raw.split(b'\0')[:-1]:
            metadata, path = record.split(b'\t', 1)
            mode, object_id, stage_text = metadata.decode('ascii').split(' ')
            stage = int(stage_text)
            if not path or stage not in (0, 1, 2, 3):
                raise ValueError('invalid path or stage')
            entries.append(IndexEntry(os.fsdecode(path), mode, object_id, stage))
    except (ValueError, UnicodeError) as error:
        raise IndexReadError(f'Malformed Git index inventory from {cwd}: {error}') from error
    return GitIndex(root.resolve(), tuple(entries))

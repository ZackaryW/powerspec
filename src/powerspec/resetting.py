"""Delete all local Powerspec and milkpan state so the next init starts from scratch.

The shared milkpan bucket is deleted whole, including content other tools put
there; that collateral is intended. The only guard is against deleting a
directory that is not recognizably a milkpan bucket.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import stat

from .consumer import discover_consumer
from .milkpan_binary import default_home

BUCKET_MARKERS = ('state.json', 'blobs', 'milkpan.toml')


@dataclass(frozen=True)
class ResetPlan:
    targets: tuple[Path, ...]
    refused: str | None = None


@dataclass(frozen=True)
class ResetResult:
    removed: tuple[str, ...]
    remaining: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.remaining


def _bucket_refusal(bucket: Path) -> str | None:
    resolved = bucket.resolve()
    if resolved == Path(resolved.anchor) or resolved == Path.home().resolve():
        return f'refusing to delete {resolved}: it is a filesystem root or the home directory'
    if resolved.is_file():
        return f'refusing to delete {resolved}: it is a file, not a milkpan bucket'
    if resolved.is_dir() and any(resolved.iterdir()) and not any((resolved / m).exists() for m in BUCKET_MARKERS):
        return f'refusing to delete {resolved}: it does not look like a milkpan bucket (set MILKPAN_HOME correctly)'
    return None


def plan_reset(cwd: Path) -> ResetPlan:
    """What a reset would delete, or why it refuses."""
    bucket = default_home()
    refusal = _bucket_refusal(bucket)
    targets = [bucket.resolve(), (Path.home() / '.powerspec').resolve()]
    try:
        consumer = discover_consumer(Path(cwd), runtime=False)
    except (OSError, ValueError):
        consumer = None
    if consumer is not None:
        state = consumer.config_path.parent / 'milkpan-state.json'
        targets += [state, state.with_suffix('.lock')]
    return ResetPlan(tuple(targets), refusal)


def apply_reset(plan: ResetPlan) -> ResetResult:
    """Delete every target, continuing past failures; report what is left."""
    if plan.refused:
        raise ValueError(plan.refused)
    removed, failed = [], []

    def retry_writable(function, path, _error):
        try:
            os.chmod(path, stat.S_IWRITE)
            function(path)
        except OSError:
            failed.append(str(path))

    for target in plan.targets:
        if not os.path.lexists(target):
            continue
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target, onexc=retry_writable)
        else:
            try:
                target.unlink()
            except OSError:
                failed.append(str(target))
        if os.path.lexists(target):
            failed.append(str(target))
        else:
            removed.append(str(target))
    return ResetResult(tuple(removed), tuple(dict.fromkeys(failed)))

"""Initialize the default store before publishing a manager inside it."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
import os
from pathlib import Path
import shutil
import tempfile
from uuid import uuid4

from zuu.case17 import FileCheckStateStore

from .catalog import ConfigurationError


def _plain(path: Path, *, directory: bool = False) -> None:
    if path.is_symlink() or path.is_junction():
        raise ConfigurationError(f'refusing linked Saucepan bootstrap path: {path}')
    if path.exists() and not (path.is_dir() if directory else path.is_file()):
        raise ConfigurationError(f'unrecognized Saucepan bootstrap path: {path}')
    if not directory and path.exists() and path.stat().st_nlink != 1:
        raise ConfigurationError(f'refusing linked Saucepan bootstrap file: {path}')


def _layout(target: Path) -> str:
    root = target.parent.parent
    _plain(root, directory=True)
    _plain(target.parent, directory=True)
    _plain(target)
    _plain(target.with_name('saucepan-check.json'))
    marker = root / 'root.json'
    _plain(marker)
    if marker.is_file():
        return 'existing'  # Contents and credentials remain Saucepan's responsibility.
    if not root.exists() or not any(root.iterdir()):
        return 'empty'
    staging = root / '.staging'
    _plain(staging, directory=True)
    initializing = staging / 'initializing.json'
    _plain(initializing)
    if initializing.is_file():
        return 'resume'  # Saucepan decides whether this interrupted root is valid.
    if {path.name for path in root.iterdir()} == {'bin'}:
        for path in target.parent.iterdir():
            if path.name not in {target.name, 'saucepan-check.json'}:
                break
            _plain(path)
        else:
            return 'binary-only'
    raise ConfigurationError(f'unrecognized uninitialized Saucepan root: {root}; preserve its contents and resolve manually')


@contextmanager
def _locked(root: Path):
    lock = root.parent / '.powerspec-saucepan-bootstrap.lock'
    root.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ConfigurationError(f'Saucepan bootstrap already in progress: {lock}; confirm its PID stopped before removing a stale lock') from error
    try:
        os.write(descriptor, str(os.getpid()).encode())
        yield
    finally:
        os.close(descriptor)
        lock.unlink()


def _copy_check(source: Path, destination: Path) -> None:
    """Relocate only a matching check identity; missing/bad cache is optional."""
    try:
        state = FileCheckStateStore(source.with_name('saucepan-check.json')).load()
        if state is not None and state.destination == os.path.normcase(os.path.abspath(source)):
            FileCheckStateStore(destination.with_name('saucepan-check.json')).save(
                replace(state, destination=os.path.normcase(os.path.abspath(destination))))
    except (OSError, ValueError):
        pass  # A later normal check can rebuild this optional cache.


def ensure_default(target: Path, *, manager_factory, downloader, validate) -> Path:
    """Preserve recognized leftovers, initialize externally, then publish."""
    from saucepan_sdk import Client

    root = target.parent.parent
    backup = None
    with _locked(root):
        layout = _layout(target)
        if layout == 'existing':
            target.parent.mkdir(exist_ok=True)
            return manager_factory(target).ensure(downloader=downloader).destination
        try:
            with tempfile.TemporaryDirectory(prefix='.powerspec-saucepan-stage-', dir=root.parent) as temporary:
                staged = Path(temporary) / target.name
                if target.exists():
                    validate(target)
                    shutil.copy2(target, staged)
                    _copy_check(target, staged)
                manager_factory(staged).ensure(downloader=downloader)
                validate(staged)
                if _layout(target) != layout:
                    raise ConfigurationError('Saucepan root changed during bootstrap; retry after resolving concurrent changes')
                if layout == 'binary-only':
                    backup = root.parent / f'.powerspec-saucepan-backup-{uuid4().hex}'
                    target.parent.rename(backup)
                Client(executable=str(staged), root=str(root)).init()
                # Do not follow a linked publication path introduced during init.
                _plain(root, directory=True)
                _plain(target.parent, directory=True)
                _plain(target)
                _plain(target.with_name('saucepan-check.json'))
                target.parent.mkdir(exist_ok=True)
                os.replace(staged, target)
                _copy_check(staged, target)
                return target
        except Exception as error:
            preserved = f'; originals preserved at {backup}' if backup is not None else ''
            raise ConfigurationError(f'Saucepan store bootstrap failed: {error}{preserved}') from error

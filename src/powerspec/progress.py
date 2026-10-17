"""Bind optional lifecycle observation and render plain stderr progress."""
from contextlib import contextmanager
from contextvars import ContextVar

import typer

from .utils.progress import Progress, ProgressEvent, Stage


_current: ContextVar[Progress | None] = ContextVar('lifecycle_progress', default=None)


def _render(event: ProgressEvent) -> None:
    label = ' '.join(event.label.splitlines())
    if event.state == 'started':
        message = f'Starting: {label}'
    elif event.state == 'waiting':
        message = f'Waiting: {label} ({event.elapsed:.0f}s elapsed; no completion reported)'
    else:
        message = f'{event.state}: {label} ({event.elapsed:.1f}s)'
        if event.detail:
            message += ': ' + ' '.join(event.detail.splitlines())
    typer.echo(message, err=True)


@contextmanager
def lifecycle_progress(emit=None, *, interval=5):
    with Progress(_render if emit is None else emit, interval=interval) as reporter:
        token = _current.set(reporter)
        try:
            yield reporter
        finally:
            _current.reset(token)


@contextmanager
def stage(label: str):
    reporter = _current.get()
    if reporter is None:
        yield Stage(label, 0, 0)
    else:
        with reporter.stage(label) as task:
            yield task

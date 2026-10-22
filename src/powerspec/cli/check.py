"""Present explicit, read-only commit preflight results."""

import json
from pathlib import Path
from typing import Annotated

import typer

from ..commit_check import check_commit
from ..presentation import to_data


def commit(
    json_output: Annotated[bool, typer.Option('--json', help='Return one structured result.')] = False,
) -> None:
    """Reject active OpenSpec changes in the whole Git index without modifying it."""
    result = check_commit(Path.cwd())
    if json_output:
        # Escapes keep arbitrary Git path names round-trippable even when a
        # Windows redirected stream uses a legacy code page.
        typer.echo(json.dumps(to_data(result), ensure_ascii=True, sort_keys=True))
    elif result.ok:
        typer.echo(f'eligible: {result.repository} (index paths only; sync, archive and zmem not verified)')
    else:
        for error in result.errors:
            typer.echo(error, err=True)
        for path in result.forbidden_paths:
            typer.echo(f'active OpenSpec entry: {path!r}', err=True)
        for path in result.unmerged_paths:
            typer.echo(f'unmerged index entry: {path!r}', err=True)
        if result.forbidden_paths:
            typer.echo('Keep active planning local. Explicitly reconcile tracked entries while preserving '
                       'local files; commit change artifacts only after successful spec sync and archive.', err=True)
    if not result.ok:
        raise typer.Exit(1)

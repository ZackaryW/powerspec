from typing import Annotated
from pathlib import Path

import typer

from ..catalog import ConfigurationError
from ..temporary import flush_current


def flush(
    change: Annotated[str | None, typer.Option(help="Change whose temporary values to clear.")] = None,
) -> None:
    """Clear all temporary values or one change-specific layer."""
    try:
        result = flush_current(Path.cwd(), change=change)
        state = "updated" if result.updated else "unchanged"
        typer.echo(f"{state}: {result.path}")
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error

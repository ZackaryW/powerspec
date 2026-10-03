"""Temporary consumer state commands."""

from pathlib import Path
from typing import Annotated

import typer

from ..catalog import ConfigurationError
from ..presentation import json_text
from ..state import read_state


def show(
    json_output: Annotated[bool, typer.Option("--json", help="Return one structured result.")] = False,
) -> None:
    """Show global and change-scoped temporary values."""
    try:
        result = read_state(Path.cwd())
        if json_output:
            typer.echo(json_text(result))
        else:
            typer.echo(f"Temporary state: {result.path}")
            typer.echo(f"Global values: {result.variables or '(none)'}")
            for change, values in result.changes.items():
                typer.echo(f"Change {change}: {values}")
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error

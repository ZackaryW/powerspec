"""Persistent consumer configuration commands."""

from pathlib import Path
from typing import Annotated

import typer

from ..catalog import ConfigurationError
from ..configuration import edit_configuration, read_configuration, set_profile
from ..presentation import json_text


def show(
    json_output: Annotated[bool, typer.Option("--json", help="Return one structured result.")] = False,
) -> None:
    """Show persistent consumer configuration."""
    try:
        result = read_configuration(Path.cwd())
        if json_output:
            typer.echo(json_text(result))
        else:
            typer.echo(f"Configuration: {result.path}")
            typer.echo(f"Profile: {result.profile or '(global profiles only)'}")
            typer.echo(f"Excluded profiles: {', '.join(result.exclude_profiles) or '(none)'}")
            for key, value in result.variables.items():
                typer.echo(f"{key} = {value!r}")
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error


def profile(
    value: Annotated[str | None, typer.Argument(help="Qualified profile; omit to select global profiles only.")] = None,
) -> None:
    """Set the selected profile, or clear it when omitted."""
    try:
        result = set_profile(Path.cwd(), value)
        state = "updated" if result.updated else "unchanged"
        typer.echo(f"{state}: {result.path} ({result.profile or 'global profiles only'})")
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error


def edit() -> None:
    """Open persistent consumer configuration in VISUAL or EDITOR."""
    try:
        path = edit_configuration(Path.cwd())
        typer.echo(f"edited: {path}")
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error

"""Present the effective read-only consumer status."""

from pathlib import Path
from typing import Annotated

import typer

from ..catalog import ConfigurationError
from ..presentation import json_text
from ..statusing import inspect_status


def status(
    json_output: Annotated[bool, typer.Option("--json", help="Return one structured result.")] = False,
) -> None:
    """Inspect effective profiles and resource availability without mutation."""
    try:
        result = inspect_status(Path.cwd())
        if json_output:
            typer.echo(json_text(result))
            return
        typer.echo(f"Consumer: {result.root}")
        typer.echo(f"Profile: {result.profile or '(global profiles only)'}")
        for label, values in (("Profiles", result.profiles), ("Contexts", result.contexts),
                              ("Traits", result.traits), ("Skills", result.skills)):
            typer.echo(f"{label}: {', '.join(values) if values else '(none)'}")
        for source in result.sources:
            detail = source.revision or source.diagnostic or ""
            typer.echo(f"Source {source.identity}: {source.status} {detail}".rstrip())
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error

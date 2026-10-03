from typing import Annotated
from pathlib import Path

import typer

from ..catalog import ConfigurationError
from ..initialization import plan_initialization, initialize


def init(
    profile: Annotated[str | None, typer.Option(help="Profile for a new consumer; existing configuration is preserved.")] = None,
) -> None:
    """Establish a Git-root OpenSpec consumer without installing agent assets."""
    try:
        cwd = Path.cwd()
        plan = plan_initialization(cwd, profile=profile)
        result = initialize(plan)
        for warning in result.warnings:
            typer.echo(f"Warning: {warning}", err=True)
        typer.echo(
            f"initialized: {result.root} ({plan.profile or 'global profiles only'}). "
            "Run pspec sync to publish contexts and pspec install --agent <agent> to install agent assets."
        )
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error

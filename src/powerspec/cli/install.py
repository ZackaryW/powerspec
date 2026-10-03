"""Install selected skills and the generic hook dispatcher for one agent."""

from pathlib import Path
from typing import Annotated

import typer

from ..catalog import ConfigurationError
from ..installation import install_consumer


def install(
    agent: Annotated[str, typer.Option(help="Target agent identifier.")],
) -> None:
    """Acquire missing selected sources and reconcile agent assets."""
    try:
        result = install_consumer(Path.cwd(), agent=agent)
        for item in result.provisioning.items:
            typer.echo(f"{item.status}: {item.ref} ({item.plan.agent}/{item.plan.scope})")
            for diagnostic in item.diagnostics:
                typer.echo(f"  {diagnostic}", err=True)
        typer.echo(f"{result.hooks.status}: Powerspec hook dispatcher ({result.hooks.agent}/user)")
        for diagnostic in result.hooks.diagnostics:
            typer.echo(f"  {diagnostic}", err=True)
        if not result.ok:
            typer.echo(
                "Installation incomplete; successful assets remain available. Resolve failures and rerun install.",
                err=True,
            )
            raise typer.Exit(1)
        typer.echo("Installation complete.")
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error

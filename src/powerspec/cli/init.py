from typing import Annotated
from pathlib import Path

import typer
from zuat.pub import SUPPORTED_AGENTS

from ..catalog import ConfigurationError
from ..initialization import plan_initialization, initialize
from ..installation import install_consumer
from ..workspace import open_workspace


def init(
    profile: Annotated[str | None, typer.Option(help="Profile for a new consumer; existing configuration is preserved.")] = None,
    agent: Annotated[str | None, typer.Option(help="Provision selected skills and hooks for this agent.")] = None,
) -> None:
    """Bootstrap a Git-root consumer, sources, and optional agent assets."""
    established = False
    try:
        if agent is not None and agent not in SUPPORTED_AGENTS:
            raise ConfigurationError("init requires a supported --agent: " + ", ".join(SUPPORTED_AGENTS))
        cwd = Path.cwd()
        plan = plan_initialization(cwd, profile=profile)
        result = initialize(plan)
        established = True
        for warning in result.warnings:
            typer.echo(f"Warning: {warning}", err=True)
        if agent is None:
            with open_workspace(result.root, agent="powerspec-init", source_mode="ensure"):
                pass
            typer.echo("Sources ready. Run pspec init --agent <agent> to provision agent assets.")
        else:
            installed = install_consumer(result.root, agent=agent)
            for item in installed.provisioning.items:
                typer.echo(f"{item.status}: {item.ref} ({item.plan.agent}/{item.plan.scope})")
                for diagnostic in item.diagnostics:
                    typer.echo(f"  {diagnostic}", err=True)
            typer.echo(f"{installed.hooks.status}: Powerspec hook dispatcher ({agent}/user)")
            for diagnostic in installed.hooks.diagnostics:
                typer.echo(f"  {diagnostic}", err=True)
            if not installed.ok:
                raise ConfigurationError("agent provisioning incomplete; see failed resources above")
        typer.echo(f"initialized: {result.root} ({plan.profile or 'global profiles only'}).")
        typer.echo("Initialization complete. Run pspec sync to publish contexts.")
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        if established:
            typer.echo("Setup incomplete; consumer files and successful assets remain available. "
                       "Resolve the failure and rerun pspec init with the same options.", err=True)
        raise typer.Exit(1) from error

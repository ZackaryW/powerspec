from typing import Annotated
from pathlib import Path

import typer

from ..catalog import Catalog, ConfigurationError
from ..consumer import find_git_root
from ..initialization import plan_initialization, initialize
from ..resources import builtin_catalog_root
from ..sources import SaucepanSources


def init(
    agent: Annotated[str | None, typer.Option(help="Target agent identifier.")] = None,
    profile: Annotated[str | None, typer.Option(help="Profile for a new consumer; existing configuration is preserved.")] = None,
) -> None:
    """Initialize the Git-root consumer and provision its selected skills."""
    try:
        cwd = Path.cwd()
        git_root = find_git_root(cwd)
        local = git_root / "openspec/.pspec" if git_root else None
        with builtin_catalog_root() as root:
            sources = {"local": local} if local is not None and local.is_dir() else {}
            catalog = Catalog(builtin=root, sources=sources,
                              git_resolver=SaucepanSources().lookup)
            plan = plan_initialization(cwd, agent=agent, catalog=catalog, profile=profile)
            typer.echo(f"Initialize {plan.root} with {plan.profile or 'global profiles'}")
            for item in plan.skills:
                target = str(item.project_root) if item.scope == "project" else "user home"
                typer.echo(f"  {item.ref}: {item.agent}/{item.scope} at {target} (profile {item.profile}; source {item.source})")
            result = initialize(plan)
        for item in result.provisioning.items:
            typer.echo(f"{item.status}: {item.ref} ({item.plan.agent}/{item.plan.scope})")
            for diagnostic in item.diagnostics:
                typer.echo(f"  {diagnostic}", err=True)
        for warning in result.warnings:
            typer.echo(f"Warning: {warning}", err=True)
        if not result.provisioning.ok:
            typer.echo("Initialization incomplete; successful installations remain available. Resolve failures and rerun init.", err=True)
            raise typer.Exit(1)
        typer.echo("Consumer initialized; selected skills are available. Run pspec sync to publish contexts.")
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error

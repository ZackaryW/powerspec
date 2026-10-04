from pathlib import Path
from typing import Annotated

import typer

from ..catalog import ConfigurationError
from ..consumer import discover_consumer
from ..resources import builtin_catalog_root
from ..sources import SaucepanSources
from ..upgrading import upgrade_consumer


def upgrade(
    agent: Annotated[str, typer.Option(help="Target agent identifier.")],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Replace selected unowned or locally modified skills through ZuAT.",
        ),
    ] = False,
) -> None:
    """Refresh selected remote skills and safely remove confirmed obsolete copies."""
    try:
        cwd = Path.cwd()
        consumer = discover_consumer(cwd, runtime=False)
        if consumer is None:
            raise ConfigurationError("no owning openspec/.pspec/config.toml within this Git repository")
        local = consumer.config_path.parent
        sources = {"local": local} if local.is_dir() else {}
        with builtin_catalog_root() as root:
            result = upgrade_consumer(
                builtin=root,
                local_sources=sources,
                consumer=consumer,
                agent=agent,
                source_store=SaucepanSources(),
                force=force,
            )
        for binding in result.refreshed:
            typer.echo(f"refreshed: {binding.identity} at {binding.resolved_revision}")
        for item in result.provisioning.items:
            typer.echo(f"{item.status}: {item.ref} ({item.plan.agent}/{item.plan.scope})")
            for diagnostic in item.diagnostics:
                typer.echo(f"  {diagnostic}", err=True)
        if result.hooks is not None:
            typer.echo(f"{result.hooks.status}: Powerspec hook dispatcher ({result.hooks.agent}/user)")
            for diagnostic in result.hooks.diagnostics:
                typer.echo(f"  {diagnostic}", err=True)
        for item in result.removed:
            typer.echo(f"removed: {item.ref} ({item.agent}/{item.scope})")
        for diagnostic in result.diagnostics:
            typer.echo(f"Error: {diagnostic}", err=True)
        if not result.ok:
            raise typer.Exit(1)
        typer.echo("Upgrade complete.")
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error

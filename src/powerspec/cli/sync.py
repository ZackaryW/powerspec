"""Publish selected compile-time contexts into the owning OpenSpec config."""
from pathlib import Path

import typer

from ..catalog import ConfigurationError
from ..conditions import Invocation, context_contributions
from ..syncing import publish
from ..sources import SaucepanSources
from ..workspace import open_workspace


def sync() -> None:
    """Reconcile selected compile-time contexts into OpenSpec config.yaml."""
    try:
        cwd = Path.cwd()
        with open_workspace(
            cwd,
            agent="powerspec-sync",
            source_mode="lookup",
            runtime=False,
            source_store=SaucepanSources(manage_binary=False),
        ) as workspace:
            contributions = context_contributions(
                workspace.bundle, workspace.consumer, Invocation(cwd)
            )
            target = workspace.consumer.config_path.parent.parent / "config.yaml"
        if not target.is_file():
            raise ConfigurationError(f"{target}: existing OpenSpec config.yaml is required; run init first")
        result = publish(target, contributions)
        state = "updated" if result.updated else "unchanged"
        typer.echo(f"{state}: {result.path}")
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error

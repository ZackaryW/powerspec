"""Publish selected compile-time contexts into the owning OpenSpec config."""
from pathlib import Path

import typer

from ..catalog import Catalog, ConfigurationError
from ..conditions import Invocation, context_contributions
from ..consumer import discover_consumer
from ..profiles import compose
from ..resources import builtin_catalog_root
from ..syncing import publish


def sync() -> None:
    """Reconcile selected compile-time contexts into OpenSpec config.yaml."""
    try:
        cwd = Path.cwd()
        consumer = discover_consumer(cwd, runtime=False)
        if consumer is None:
            raise ConfigurationError("no owning openspec/.pspec/config.toml within this Git repository")
        if consumer.config.profile is None:
            raise ConfigurationError(f"{consumer.config_path}: profile is required for sync")
        with builtin_catalog_root() as root:
            catalog = Catalog(builtin=root)
            bundle = compose(
                catalog,
                consumer.config.profile,
                agent="powerspec-sync",
                project_root=consumer.git_root,
                exclude_profiles=consumer.config.exclude_profiles,
            )
            contributions = context_contributions(bundle, consumer, Invocation(cwd))
        target = consumer.config_path.parent.parent / "config.yaml"
        if not target.is_file():
            raise ConfigurationError(f"{target}: existing OpenSpec config.yaml is required; run init first")
        result = publish(target, contributions)
        state = "updated" if result.updated else "unchanged"
        typer.echo(f"{state}: {result.path}")
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error

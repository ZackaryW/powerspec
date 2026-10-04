from typing import Annotated
from pathlib import Path

import typer

from ..catalog import Catalog, ConfigurationError
from ..consumer import discover_consumer
from ..hooks import callback_for, dispatch, serialize
from ..resources import builtin_catalog_root
from ..sources import SaucepanSources


def hook(
    event: Annotated[str, typer.Argument(help="Hook event name.", metavar="EVENT")],
    agent: Annotated[str, typer.Option(help="Invoking native agent identifier.")],
    change: Annotated[str | None, typer.Option(help="Explicit active change name.")] = None,
) -> None:
    """Return hook guidance from the current directory without reading stdin."""
    try:
        callback_for(agent, event)
        cwd = Path.cwd()
        consumer = discover_consumer(cwd)
        with builtin_catalog_root() as root:
            sources = ({"local": consumer.config_path.parent}
                       if consumer is not None and consumer.config_path.parent.is_dir() else {})
            catalog = Catalog(
                builtin=root,
                sources=sources,
                git_resolver=SaucepanSources(manage_binary=False).lookup,
            )
            diagnostics = []
            guidance = dispatch(logical_event=event, agent=agent, cwd=cwd,
                                catalog=catalog, change=change,
                                diagnostics=diagnostics)
        for diagnostic in diagnostics:
            typer.echo(f"Warning: {diagnostic}", err=True)
        output = serialize(agent, event, guidance)
        if output is not None:
            typer.echo(output)
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error

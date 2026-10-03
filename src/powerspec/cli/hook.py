from typing import Annotated
from pathlib import Path
import json
import sys

import typer

from ..catalog import Catalog, ConfigurationError
from ..consumer import discover_consumer
from ..hooks import dispatch, serialize
from ..resources import builtin_catalog_root
from ..sources import SaucepanSources


def hook(
    event: Annotated[str, typer.Argument(help="Hook event name.", metavar="EVENT")],
    agent: Annotated[str, typer.Option(help="Invoking native agent identifier.")],
    change: Annotated[str | None, typer.Option(help="Explicit active change name.")] = None,
) -> None:
    """Return current consumer trait guidance for one native callback."""
    try:
        try:
            payload = json.load(sys.stdin)
        except (json.JSONDecodeError, UnicodeError) as error:
            raise ConfigurationError(f"invalid native hook JSON input: {error}") from error
        cwd = payload.get("cwd") if isinstance(payload, dict) else None
        consumer = discover_consumer(Path(cwd)) if isinstance(cwd, str) else None
        with builtin_catalog_root() as root:
            sources = ({"local": consumer.config_path.parent}
                       if consumer is not None and consumer.config_path.parent.is_dir() else {})
            catalog = Catalog(builtin=root, sources=sources,
                              git_resolver=SaucepanSources().lookup)
            guidance = dispatch(logical_event=event, agent=agent, payload=payload,
                                catalog=catalog, change=change)
        output = serialize(agent, event, guidance)
        if output is not None:
            typer.echo(output)
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error

"""Present read-only prerequisite diagnostics."""

from pathlib import Path
from typing import Annotated

import typer

from ..doctoring import doctor_consumer
from ..presentation import json_text


def doctor(
    json_output: Annotated[bool, typer.Option("--json", help="Return one structured result.")] = False,
    agent: Annotated[str | None, typer.Option(help="Inspect guidance delivery for codex or claude.")] = None,
) -> None:
    """Check the consumer and required tools without repairing them."""
    if agent is not None and agent not in {'codex', 'claude'}:
        raise typer.BadParameter('supported delivery agents are codex and claude', param_hint='--agent')
    result = doctor_consumer(Path.cwd(), agent=agent)
    if json_output:
        typer.echo(json_text({"ok": result.ok, "checks": result.checks}))
    else:
        for item in result.checks:
            typer.echo(f"{item.status}: {item.name} - {item.detail}")
    if not result.ok:
        raise typer.Exit(1)

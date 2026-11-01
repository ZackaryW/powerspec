"""Present read-only prerequisite diagnostics, or deliberately reset local state."""

from pathlib import Path
import sys
from typing import Annotated

import typer

from ..doctoring import doctor_consumer
from ..presentation import json_text
from ..resetting import apply_reset, plan_reset


def doctor(
    json_output: Annotated[bool, typer.Option("--json", help="Return one structured result.")] = False,
    agent: Annotated[str | None, typer.Option(help="Inspect guidance delivery for codex or claude.")] = None,
    force_reset: Annotated[bool, typer.Option("--force-reset", help="Delete the whole shared milkpan bucket, all of ~/.powerspec and this project's selection state, so the next init starts from scratch.")] = False,
    yes: Annotated[bool, typer.Option("--yes", help="Confirm --force-reset without prompting.")] = False,
) -> None:
    """Check the consumer and required tools without repairing them."""
    if force_reset:
        _reset(json_output=json_output, yes=yes)
        return
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


def _reset(*, json_output: bool, yes: bool) -> None:
    plan = plan_reset(Path.cwd())
    if plan.refused:
        typer.echo(f"Error: {plan.refused}; nothing was deleted", err=True)
        raise typer.Exit(1)
    typer.echo("Reset deletes (including content other tools stored in the milkpan bucket):", err=True)
    for target in plan.targets:
        typer.echo(f"  {target}", err=True)
    if not yes:
        if not sys.stdin.isatty():
            typer.echo("Error: confirmation required; rerun with --yes. Nothing was deleted.", err=True)
            raise typer.Exit(1)
        if not typer.confirm("Delete these?", default=False, err=True):
            typer.echo("Nothing was deleted.", err=True)
            raise typer.Exit(1)
    result = apply_reset(plan)
    if json_output:
        typer.echo(json_text({"ok": result.ok, "reset": {"removed": result.removed, "remaining": result.remaining}}))
    else:
        for path in result.removed:
            typer.echo(f"removed: {path}")
        for path in result.remaining:
            typer.echo(f"remaining: {path}")
        typer.echo("Run pspec init to re-establish." if result.ok
                   else "Some paths could not be removed (still in use?); retry after closing them.")
    if not result.ok:
        raise typer.Exit(1)

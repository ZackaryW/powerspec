"""Workset input grammar and human/JSON presentation."""
from pathlib import Path
from typing import Annotated

import typer
from typer.core import TyperCommand

from ..presentation import json_text
from ..workset_openspec import OpenSpec
from ..worksets import add_source, parse_overrides
from ..workset_launch import launch as launch_workset
from .. import workset_defaults


class WorksetCommand(TyperCommand):
    def parse_args(self, ctx, args):
        json_requested = "--json" in args
        try:
            for index, token in enumerate(args):
                if token in ("--branch", "--name", "--store", "--change", "--path"):
                    if index + 1 == len(args) or args[index + 1].startswith("--"):
                        raise typer.BadParameter(f"Missing value for {token}")
            return super().parse_args(ctx, args)
        except Exception as error:
            if getattr(error, "exit_code", None) == 2 and json_requested:
                typer.echo(json_text({"ok": False, "stage": "arguments", "errors": [str(error)]}))
                typer.echo(str(error), err=True)
                raise typer.Exit(2) from error
            raise


app = typer.Typer(help="Spawn implementation worktrees from OpenSpec worksets.", cls=typer.core.TyperGroup)


def present(result, json_output):
    if json_output:
        typer.echo(json_text(result))
    else:
        if "action" in result:
            typer.echo(f"{result['action']}: {result.get('name')} at {result.get('path')}")
        for member in result.get("members", []):
            typer.echo(f"{member['action']}: {member['label']} [{member['branch']}] {member['path']}")
        for store in result.get("stores", []):
            typer.echo(f"store: {store['original_id']} -> {store['id']} at {store['path']}")
        for effect in result.get("effects", []):
            typer.echo(f"{effect['action']}: {effect['path']}")
        default = result.get("default")
        if isinstance(default, dict):
            detail = default.get("label") or default.get("reason")
            typer.echo(f"default {default['action']}: {detail}")
        elif default:
            typer.echo(f"default: {default}")
        transfer = result.get("transfer")
        if transfer:
            typer.echo(f"{transfer['action']}: {transfer['source']} -> {transfer['destination']}")
        if result.get("workspace_ready"):
            typer.echo(f"Workspace ready: {result['name']}")
            typer.echo(result["opening_command"])
    for error in result.get("errors", []):
        typer.echo(f"{result.get('stage', 'error')}: {error}", err=True)


@app.command(cls=WorksetCommand)
def add(
    name: Annotated[str, typer.Argument(help="OpenSpec source workset name.")],
    path: Annotated[Path, typer.Option(help="Existing Git repository or subfolder.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit one JSON result.")] = False,
):
    """Register a Git repository as a source workset member."""
    try:
        result = {"ok": True, **add_source(OpenSpec(Path.cwd()), name, path)}
    except (ValueError, OSError) as error:
        result = {"ok": False, "stage": "registration", "errors": [str(error)]}
    present(result, json_output)
    if not result["ok"]:
        raise typer.Exit(1)


@app.command(cls=WorksetCommand, context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def launch(
    ctx: typer.Context,
    source: Annotated[str, typer.Argument(help="Source OpenSpec workset.")],
    branch: Annotated[str, typer.Option(help="Shared target branch. New branches start at local main.")],
    name: Annotated[str | None, typer.Option(help="Output workset name override.")] = None,
    change: Annotated[str | None, typer.Option(help="Active change to transfer.")] = None,
    store: Annotated[str | None, typer.Option(help="Original source store ID; requires --change.")] = None,
    keep_source: Annotated[bool, typer.Option(help="Copy instead of move; requires --change.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit one JSON result, including partial failures.")] = False,
):
    """Launch all repositories. Overrides: --repoN LABEL --branchN BRANCH --remoteN REMOTE/REF --worktreeN DIRECTORY."""
    try:
        if (store or keep_source) and not change:
            raise ValueError("--store and --keep-source require --change")
        overrides = parse_overrides(ctx.args)
    except ValueError as error:
        present({"ok": False, "stage": "arguments", "errors": [str(error)]}, json_output)
        raise typer.Exit(2) from error
    result = launch_workset(OpenSpec(Path.cwd()), source, branch, overrides, name=name,
                            change=change, store=store, keep_source=keep_source)
    present(result, json_output)
    if not result["ok"]:
        raise typer.Exit(1)


def present_default(result, json_output):
    if json_output:
        typer.echo(json_text(result))
    elif result["ok"]:
        name = result["workset"]
        if result.get("default") is None:
            typer.echo(f"{result['action']}: {name} has no default" if result["action"] != "cleared"
                       else f"cleared: {name}")
        else:
            typer.echo(f"{result['action']}: {name} -> {result['default']} ({result['path']}) [{result['status']}]")
            if result["status"].startswith("stale"):
                typer.echo(f"Set it again with: pspec workset default {name} <member-label>")
    for error in result.get("errors", []):
        typer.echo(f"{result.get('stage', 'error')}: {error}", err=True)


@app.command(cls=WorksetCommand)
def default(
    name: Annotated[str, typer.Argument(help="OpenSpec workset name.")],
    label: Annotated[str | None, typer.Argument(help="Member label to make the default.")] = None,
    clear: Annotated[bool, typer.Option("--clear", help="Remove the workset's default.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit one JSON result.")] = False,
):
    """Show, set, or clear the member agents fall back to in multi-project sessions."""
    try:
        result = workset_defaults.default_workset(OpenSpec(Path.cwd()), name, label, clear=clear)
    except (ValueError, OSError) as error:
        result = {"ok": False, "stage": "default", "errors": [str(error)]}
    present_default(result, json_output)
    if not result["ok"]:
        raise typer.Exit(1)

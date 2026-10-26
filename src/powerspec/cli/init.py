from enum import Enum
from typing import Annotated
from pathlib import Path
import sys

import typer
from zuat.pub import SUPPORTED_AGENTS

from ..catalog import ConfigurationError, MetadataUnavailable
from ..initialization import plan_initialization, initialize
from ..installation import install_consumer
from ..workspace import open_workspace
from ..progress import lifecycle_progress, paused, stage


class Scope(str, Enum):
    local = "local"
    global_ = "global"
    all = "all"


def _interactive() -> bool:
    return sys.stdin.isatty() and sys.stderr.isatty()


def _confirm_replacement(conflicts) -> bool:
    """Ask once, on stderr, before replacing every reported conflict."""
    if not _interactive():
        return False
    with paused():
        typer.echo(f"{len(conflicts)} selected skills differ from Powerspec's copies:", err=True)
        for item in conflicts:
            typer.echo(f"  {item.plan.name} ({item.plan.agent}/{item.plan.scope})", err=True)
        typer.echo("Originals are backed up by ZuAT and can be restored.", err=True)
        try:
            return typer.confirm("Replace them?", default=False, err=True)
        except typer.Abort:
            return False


def init(
    profile: Annotated[str | None, typer.Option(help="Profile for a new consumer; existing configuration is preserved.")] = None,
    agent: Annotated[str | None, typer.Option(help="Provision selected skills and hooks for this agent.")] = None,
    force: Annotated[bool, typer.Option('--force', help='Refresh sources, authorize verified Saucepan migration, and with --agent recoverably replace conflicting selected skills and repair matching hook receipts.')] = False,
    scope: Annotated[Scope, typer.Option('--scope', help='local: consumer and sources only; global: agent skills and hooks from existing selections; all: both.')] = Scope.all,
) -> None:
    """Bootstrap a Git-root consumer, sources, and optional agent assets."""
    with lifecycle_progress():
        established = False
        try:
            if agent is not None and agent not in SUPPORTED_AGENTS:
                raise ConfigurationError("init requires a supported --agent: " + ", ".join(SUPPORTED_AGENTS))
            if scope is Scope.local and agent is not None:
                raise ConfigurationError("--scope local does not provision agent assets; omit --agent")
            if scope is Scope.global_ and agent is None:
                raise ConfigurationError("--scope global requires --agent")
            cwd = Path.cwd()
            if scope is Scope.global_:
                with stage('Checking consumer'):
                    plan = plan_initialization(cwd, profile=profile)
                    if not plan.config_path.exists():
                        raise ConfigurationError("no consumer to provision; run pspec init or pspec init --scope local first")
                root = plan.root
            else:
                with stage('Establishing consumer'):
                    plan = plan_initialization(cwd, profile=profile)
                    result = initialize(plan)
                for warning in result.warnings:
                    typer.echo(f"Warning: {warning}", err=True)
                root = result.root
            established = True
            if agent is None:
                with open_workspace(root, agent="powerspec-init", source_mode="refresh" if force else "ensure",
                                    migrate_unmanaged=force) as workspace:
                    if callable(getattr(workspace.source_store, 'commit', None)):
                        with stage('Saving source selections'):
                            workspace.source_store.commit()
                typer.echo("Sources ready. Run pspec init --agent <agent> to provision agent assets.")
            else:
                with stage('Preparing sources and agent assets') as task:
                    sourcing = scope is not Scope.global_
                    try:
                        installed = install_consumer(root, agent=agent, refresh_sources=force and sourcing,
                                                     migrate_unmanaged=force and sourcing,
                                                     lookup_sources=not sourcing,
                                                     repair_hooks=force, replace_skills=force,
                                                     confirm_replacement=None if force else _confirm_replacement)
                    except MetadataUnavailable as error:
                        if sourcing:
                            raise
                        raise ConfigurationError(f"{error}; run pspec init or pspec init --scope local first") from error
                    if not installed.ok:
                        task.result('failed', 'agent provisioning incomplete')
                for item in installed.provisioning.items:
                    typer.echo(f"{item.status}: {item.ref} ({item.plan.agent}/{item.plan.scope})")
                    for diagnostic in item.diagnostics:
                        typer.echo(f"  {diagnostic}", err=True)
                    if item.replaced and item.operation_id:
                        typer.echo(f"  ZuAT skill operation: {item.operation_id}")
                typer.echo(f"{installed.hooks.status}: Powerspec hook dispatcher ({agent}/user)")
                for diagnostic in installed.hooks.diagnostics:
                    typer.echo(f"  {diagnostic}", err=True)
                if installed.hooks.operation_id:
                    typer.echo(f"  ZuAT hook operation: {installed.hooks.operation_id}", err=not installed.hooks.ok)
                if installed.provisioning.replaceable:
                    raise ConfigurationError("agent provisioning incomplete; replace conflicting skills with "
                                             f"pspec init --agent {agent} --force")
                if not installed.ok:
                    raise ConfigurationError("agent provisioning incomplete; see failed resources above")
            typer.echo(f"initialized: {root} ({plan.profile or 'global profiles only'}).")
            typer.echo("Initialization complete. Run pspec sync to publish contexts.")
        except (ConfigurationError, OSError, ValueError) as error:
            typer.echo(f"Error: {error}", err=True)
            if established:
                typer.echo("Setup incomplete; consumer files and successful assets remain available. "
                           "Resolve the failure and rerun pspec init with the same options.", err=True)
            raise typer.Exit(1) from error

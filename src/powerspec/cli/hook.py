from typing import Annotated
from pathlib import Path
import sys

import typer

from ..catalog import Catalog, ConfigurationError
from ..consumer import discover_consumer
from ..hooks import callback_for, dispatch, serialize
from ..resources import builtin_catalog_root
from ..sources import SaucepanSources
from ..utils.sections import compose_sections
from ..utils.stdin_payload import read_json_object
from .. import workset_defaults

# Leaves the one-second metadata budget and the five-second handler limit intact.
PAYLOAD_TIMEOUT = 0.5
MULTI_PROJECT_INTRO = (
    "This session includes several Powerspec projects. Each section below applies only to "
    "its project. Follow only the section for the project you are actively implementing "
    "or updating changes in."
)


def _payload_workspaces() -> tuple[list[Path], list[str]] | None:
    """Existing workspace directories and every listed path, or ``None`` for a terminal."""
    stream = sys.stdin
    try:
        if stream is not None and stream.isatty():
            return None
    except (OSError, ValueError):
        pass
    document = read_json_object(stream, PAYLOAD_TIMEOUT) if stream is not None else None
    paths = document.get("workspacePaths") if document is not None else None
    if not isinstance(paths, list) or not all(isinstance(item, str) for item in paths):
        typer.echo("Warning: hook payload has no workspacePaths list; no guidance delivered", err=True)
        return [], []
    existing = []
    for item in paths:
        if Path(item).is_dir():
            existing.append(Path(item))
        else:
            typer.echo(f"Warning: hook payload workspace is not a directory: {item}", err=True)
    if not existing:
        typer.echo("Warning: hook payload names no existing workspace directory; no guidance delivered",
                   err=True)
    return existing, paths


def _guidance(root: Path, cwd: Path, consumer, event: str, agent: str, change: str | None) -> str | None:
    sources = ({"local": consumer.config_path.parent}
               if consumer is not None and consumer.config_path.parent.is_dir() else {})
    catalog = Catalog(
        builtin=root,
        sources=sources,
        git_resolver=SaucepanSources(manage_binary=False,
            consumer_path=consumer.config_path if consumer else None).lookup,
    )
    diagnostics = []
    guidance = dispatch(logical_event=event, agent=agent, cwd=cwd,
                        catalog=catalog, change=change, diagnostics=diagnostics)
    for diagnostic in diagnostics:
        typer.echo(f"Warning: {diagnostic}", err=True)
    return guidance


def _workset_default(listed: list[str]):
    """The stored default whose member snapshot is exactly this session, read locally."""
    path = workset_defaults.defaults_file()
    try:
        entries = workset_defaults.load(path)
    except (workset_defaults.DefaultsError, OSError) as error:
        typer.echo(f"Warning: {error}", err=True)
        return None
    _, entry, ambiguous = workset_defaults.match(entries, listed)
    if ambiguous:
        typer.echo(f"Warning: workset defaults are ambiguous for this session: {', '.join(ambiguous)}",
                   err=True)
    return entry


def _several(root: Path, workspaces: list[Path], listed: list[str], event: str, agent: str,
             change: str | None) -> str | None:
    """One labeled section per distinct consumer; a failing consumer omits only itself."""
    default = _workset_default(listed)
    marked = workset_defaults.normalize(default.path) if default else None
    sections, seen, found, failed = [], set(), 0, 0
    for workspace in workspaces:
        try:
            consumer = discover_consumer(workspace)
            if consumer is None or consumer.config_path in seen:
                continue
            seen.add(consumer.config_path)
            found += 1
            body = _guidance(root, workspace, consumer, event, agent, change)
        except (ConfigurationError, OSError, ValueError) as error:
            found += 1
            failed += 1
            typer.echo(f"Error: {workspace}: {error}", err=True)
            continue
        project = consumer.git_root
        label = f"{project.name} ({project})"
        if marked in {workset_defaults.normalize(workspace), workset_defaults.normalize(project)}:
            label += " (default)"
        sections.append((label, body))
    if found and failed == found:
        raise typer.Exit(1)
    intro = MULTI_PROJECT_INTRO
    if default is not None:
        intro += (" If you cannot determine which project applies, use the default project "
                  f"{default.label} ({default.path}).")
    return compose_sections(intro, sections) or None


def hook(
    event: Annotated[str, typer.Argument(help="Hook event name.", metavar="EVENT")],
    agent: Annotated[str, typer.Option(help="Invoking native agent identifier.")],
    change: Annotated[str | None, typer.Option(help="Explicit active change name.")] = None,
    stdin_workspace: Annotated[bool, typer.Option(
        "--stdin-workspace",
        help="Read the session workspace from the host's JSON payload (Antigravity only).",
    )] = False,
) -> None:
    """Return hook guidance from the current directory, or from the payload's workspaces."""
    try:
        callback = callback_for(agent, event)
        if stdin_workspace and not callback.payload_workspace:
            raise ConfigurationError(f"{agent!r} hooks run in the session directory; --stdin-workspace is not supported")
        selected = _payload_workspaces() if stdin_workspace else None
        with builtin_catalog_root() as root:
            if selected is None:
                cwd = Path.cwd()
                guidance = _guidance(root, cwd, discover_consumer(cwd), event, agent, change)
            else:
                workspaces, listed = selected
                if not workspaces:
                    return
                if len(listed) == 1:
                    guidance = _guidance(root, workspaces[0], discover_consumer(workspaces[0]),
                                         event, agent, change)
                else:
                    guidance = _several(root, workspaces, listed, event, agent, change)
        output = serialize(agent, event, guidance)
        if output is not None:
            typer.echo(output)
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error

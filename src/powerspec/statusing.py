"""Read a consumer's effective selection without changing materializations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .catalog import ConfigurationError
from .workspace import open_workspace


@dataclass(frozen=True)
class SourceStatus:
    identity: str
    status: str
    revision: str | None = None
    diagnostic: str | None = None


@dataclass(frozen=True)
class StatusResult:
    root: Path
    config_path: Path
    profile: str | None
    profiles: tuple[str, ...]
    contexts: tuple[str, ...]
    traits: tuple[str, ...]
    skills: tuple[str, ...]
    sources: tuple[SourceStatus, ...]


def inspect_status(cwd: Path, *, source_store=None) -> StatusResult:
    """Inspect selected resources and current Saucepan availability only."""
    with open_workspace(
        cwd,
        agent="powerspec-status",
        source_mode="lookup",
        source_store=source_store,
        resolve_skills=False,
    ) as workspace:
        statuses = []
        for identity, recipe in workspace.bundle.sources.items():
            try:
                binding = workspace.source_store.lookup(identity, dict(recipe))
            except (ConfigurationError, OSError, ValueError) as error:
                statuses.append(SourceStatus(identity, "unavailable", diagnostic=str(error)))
            else:
                statuses.append(SourceStatus(identity, "available", binding.resolved_revision))
        selection = workspace.bundle.selection
        return StatusResult(
            workspace.consumer.git_root,
            workspace.consumer.config_path,
            workspace.consumer.config.profile,
            tuple(item.ref for item in workspace.bundle.profiles),
            tuple(item.ref for item in workspace.bundle.contexts),
            tuple(item.ref for item in workspace.bundle.traits),
            tuple(sorted(ref for kind, ref in selection if kind == "skill")),
            tuple(statuses),
        )

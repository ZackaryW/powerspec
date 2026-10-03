"""Acquire selected sources and reconcile one agent installation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from zuat.pub import SUPPORTED_AGENTS

from .catalog import ConfigurationError
from .provisioning import (
    HookOutcome,
    ProvisionResult,
    plan_skills,
    provision_hooks,
    provision_skills,
)
from .workspace import open_workspace


@dataclass(frozen=True)
class InstallationResult:
    root: Path
    profile: str | None
    provisioning: ProvisionResult
    hooks: HookOutcome

    @property
    def ok(self) -> bool:
        return self.provisioning.ok and self.hooks.ok


def install_consumer(
    cwd: Path,
    *,
    agent: str,
    home: Path | None = None,
    registry: Path | None = None,
    source_store=None,
) -> InstallationResult:
    """Ensure sources, install selected skills, and reconcile one dispatcher."""
    if agent not in SUPPORTED_AGENTS:
        raise ConfigurationError(
            "provisioning requires a supported --agent: " + ", ".join(SUPPORTED_AGENTS)
        )
    with open_workspace(
        cwd,
        agent=agent,
        source_mode="ensure",
        source_store=source_store,
    ) as workspace:
        plans = plan_skills(workspace.bundle)
        provisioning = provision_skills(plans, home=home, registry=registry)
        hooks = provision_hooks(agent, home=home, registry=registry)
        return InstallationResult(
            workspace.consumer.git_root,
            workspace.consumer.config.profile,
            provisioning,
            hooks,
        )

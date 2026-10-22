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
from .sources import SaucepanSources
from .progress import stage


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
    repair_hooks: bool = False,
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
        with stage(f'Reconciling {agent} hooks') as task:
            hooks = provision_hooks(agent, home=home, registry=registry, repair_hooks=repair_hooks)
            task.result(hooks.status, '; '.join(hooks.diagnostics))
        if isinstance(workspace.source_store, SaucepanSources):
            if provisioning.ok and hooks.ok:
                with stage('Saving source selections'):
                    workspace.source_store.commit()
            else:
                with stage('Retaining recovery state after incomplete provisioning'):
                    workspace.source_store.reject()
        return InstallationResult(
            workspace.consumer.git_root,
            workspace.consumer.config.profile,
            provisioning,
            hooks,
        )

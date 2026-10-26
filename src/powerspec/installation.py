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
    refresh_sources: bool = False,
    lookup_sources: bool = False,
    migrate_unmanaged: bool = False,
    replace_skills: bool = False,
    confirm_replacement=None,
) -> InstallationResult:
    """Ensure sources, install selected skills, and reconcile one dispatcher.

    ``confirm_replacement`` receives the completely inspected conflicts left by
    an unforced pass; a true answer replaces only those through ZuAT's forced
    path, which rechecks each target inside its own preflight.
    """
    if agent not in SUPPORTED_AGENTS:
        raise ConfigurationError(
            "provisioning requires a supported --agent: " + ", ".join(SUPPORTED_AGENTS)
        )
    with open_workspace(
        cwd,
        agent=agent,
        source_mode="lookup" if lookup_sources else "refresh" if refresh_sources else "ensure",
        migrate_unmanaged=migrate_unmanaged,
        source_store=source_store,
    ) as workspace:
        plans = plan_skills(workspace.bundle)
        if isinstance(workspace.source_store, SaucepanSources):
            # Recovery commands need a published selection, so a first one must
            # not depend on agent provisioning succeeding.
            workspace.source_store.commit_new()
        provisioning = provision_skills(plans, home=home, registry=registry, force=replace_skills)
        conflicts = provisioning.replaceable
        if conflicts and confirm_replacement is not None and confirm_replacement(conflicts):
            retried = iter(provision_skills([item.plan for item in conflicts], home=home,
                                            registry=registry, force=True).items)
            provisioning = ProvisionResult(tuple(next(retried) if item.replaceable else item
                                                 for item in provisioning.items))
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

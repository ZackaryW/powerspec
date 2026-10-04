"""Explicit remote refresh, provisioning, and recoverable obsolete removal."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from zuat.pub import AssetSelector, ZuatRequest, inspect_asset, restore_all, uninstall

from .catalog import Catalog, ConfigurationError, git_skill_source, is_git_skill_reference
from .profiles import compose
from .provisioning import (
    HookOutcome,
    ProvisionResult,
    SkillPlan,
    plan_skills,
    provision_hooks,
    provision_skills,
)
from .sources import SaucepanSources, SourceBinding


@dataclass(frozen=True)
class UpgradeResult:
    status: str
    refreshed: tuple[SourceBinding, ...] = ()
    provisioning: ProvisionResult = ProvisionResult(())
    hooks: HookOutcome | None = None
    removed: tuple[SkillPlan, ...] = ()
    diagnostics: tuple[str, ...] = ()

    @property
    def ok(self):
        return self.status == "success"


def _remote_refs(bundle):
    return tuple(dict.fromkeys(
        ref
        for profile in bundle.profiles
        for ref in profile.data.get("skills", [])
        if is_git_skill_reference(ref)
    ))


def _source_identity(ref):
    return git_skill_source(ref)


def _target(plan):
    return plan.agent, plan.scope, plan.project_root, plan.name


def _restore(operation_id, agent, *, root, home, project_root):
    return restore_all(
        operation_id,
        AssetSelector(agent=agent, kind="skill", present=None),
        root=root,
        home=home,
        project_root=project_root,
    )


def _verify_removed(plans, *, root, home, project_root):
    for plan in plans:
        observed = inspect_asset(
            plan.asset(), root=root, home=home, project_root=project_root
        )
        if observed.classification != "absent" or observed.owned:
            raise ConfigurationError(
                f"removal finalization did not establish absence for {plan.ref}: "
                f"{observed.classification}"
            )


def upgrade_consumer(
    *,
    builtin: Path,
    consumer,
    agent: str,
    local_sources=None,
    source_store=None,
    home: Path | None = None,
    registry: Path | None = None,
    force: bool = False,
    provision=provision_skills,
    reconcile_hooks=provision_hooks,
    inspect=inspect_asset,
    remove=uninstall,
    restore=_restore,
    finalize=_verify_removed,
) -> UpgradeResult:
    """Refresh every selected Git source and commit removals at the final boundary."""
    store = source_store or SaucepanSources()
    source_roots = dict(local_sources or {})
    compose_args = dict(
        selected=consumer.config.profile,
        agent=agent,
        project_root=consumer.git_root,
        exclude_profiles=consumer.config.exclude_profiles,
    )
    try:
        old_catalog = Catalog(
            builtin=builtin, sources=source_roots, git_resolver=store.lookup
        )
        old_bundle = compose(old_catalog, **compose_args)
        refs = _remote_refs(old_bundle)
        refreshed = {}
        for identity in dict.fromkeys(map(_source_identity, refs)):
            refreshed[identity] = store.acquire(identity, old_bundle.sources[identity])
        new_catalog = Catalog(
            builtin=builtin, sources=source_roots, gitsources=refreshed,
            git_resolver=store.lookup,
        )
        allowed_empty = tuple(
            ref for ref in refs
            if not new_catalog.select("skill", ref, allow_empty=True)
        )
        new_bundle = compose(
            new_catalog, **compose_args, empty_skill_selectors=allowed_empty
        )
        old_plans = plan_skills(SimpleNamespace(
            skills=tuple(item for item in old_bundle.skills
                         if is_git_skill_reference(item.resource.ref))
        ))
        new_plans = plan_skills(new_bundle)
    except (ConfigurationError, OSError, ValueError) as error:
        return UpgradeResult("failed", diagnostics=(str(error),))

    provisioned = provision(
        new_plans, home=home, registry=registry, force=force
    )
    if not provisioned.ok:
        return UpgradeResult(
            "failed", refreshed=tuple(refreshed.values()), provisioning=provisioned,
            diagnostics=("selected skill provisioning did not complete; obsolete copies were preserved",),
        )
    hooked = reconcile_hooks(agent, home=home, registry=registry)
    if not hooked.ok:
        return UpgradeResult(
            "failed",
            refreshed=tuple(refreshed.values()),
            provisioning=provisioned,
            hooks=hooked,
            diagnostics=(*hooked.diagnostics, "hook reconciliation did not complete; obsolete copies were preserved"),
        )

    selected_targets = {
        (item.agent, item.scope, item.project_root, item.resource.name)
        for item in new_bundle.skills
    }
    obsolete = tuple(plan for plan in old_plans if _target(plan) not in selected_targets)
    if not obsolete:
        return UpgradeResult(
            "success",
            refreshed=tuple(refreshed.values()),
            provisioning=provisioned,
            hooks=hooked,
        )

    context = dict(root=registry, home=home, project_root=consumer.git_root)
    asset_refs = []
    diagnostics = []
    for plan in obsolete:
        observed = inspect(plan.asset(), **context)
        if not (observed.classification == "current" and observed.owned
                and observed.source_matches and observed.asset_ref is not None):
            diagnostics.append(
                f"obsolete copy is not a verified unchanged ZuAT-managed asset: {plan.ref}"
            )
        else:
            asset_refs.append(observed.asset_ref.id)
    if diagnostics:
        return UpgradeResult(
            "failed", refreshed=tuple(refreshed.values()), provisioning=provisioned,
            hooks=hooked,
            diagnostics=tuple(diagnostics) + ("obsolete copies were preserved",),
        )

    removal = remove(
        ZuatRequest(agents=(agent,), asset_refs=tuple(asset_refs)), **context
    )
    if not removal.ok:
        if removal.operation_id is not None:
            restored = restore(removal.operation_id, agent, **context)
            if not restored.ok:
                return UpgradeResult(
                    "partial", refreshed=tuple(refreshed.values()), provisioning=provisioned,
                    hooks=hooked,
                    diagnostics=tuple(removal.diagnostics) + tuple(restored.diagnostics)
                    + ("ZuAT could not restore the failed removal operation",),
                )
        return UpgradeResult(
            "failed", refreshed=tuple(refreshed.values()), provisioning=provisioned,
            hooks=hooked,
            diagnostics=tuple(removal.diagnostics) + ("obsolete copies were restored or never removed",),
        )

    try:
        finalize(obsolete, **context)
    except (ConfigurationError, OSError, ValueError) as error:
        restored = restore(removal.operation_id, agent, **context) if removal.operation_id else None
        if restored is None or not restored.ok:
            extra = tuple(restored.diagnostics) if restored is not None else ()
            return UpgradeResult(
                "partial", refreshed=tuple(refreshed.values()), provisioning=provisioned,
                hooks=hooked,
                diagnostics=(str(error), *extra, "ZuAT could not restore removal after finalization failed"),
            )
        return UpgradeResult(
            "failed", refreshed=tuple(refreshed.values()), provisioning=provisioned,
            hooks=hooked,
            diagnostics=(str(error), "removal finalization failed; obsolete copies were restored"),
        )
    return UpgradeResult(
        "success",
        refreshed=tuple(refreshed.values()),
        provisioning=provisioned,
        hooks=hooked,
        removed=obsolete,
    )

"""Provision explicit profile targets through ZuAT's native ownership checks."""
from dataclasses import dataclass
from pathlib import Path

from zuat.pub import SUPPORTED_AGENTS, AssetInput, ZuatRequest, inspect_asset, install, locate_skill

from .catalog import ConfigurationError


@dataclass(frozen=True)
class SkillPlan:
    ref: str
    name: str
    source: Path
    profile: str
    agent: str
    scope: str
    project_root: Path | None

    def asset(self):
        return AssetInput(agent=self.agent, kind="skill", scope=self.scope,
                          name=self.name, source=str(self.source))


@dataclass(frozen=True)
class SkillOutcome:
    ref: str
    status: str
    plan: SkillPlan
    diagnostics: tuple[str, ...] = ()
    operation_id: str | None = None


@dataclass(frozen=True)
class ProvisionResult:
    items: tuple[SkillOutcome, ...]

    @property
    def ok(self):
        return all(item.status in {"installed", "reused"} for item in self.items)


def plan_skills(bundle) -> tuple[SkillPlan, ...]:
    """Validate every descriptor before any registry or native installation writes."""
    plans = []
    for target in bundle.skills:
        if target.agent not in SUPPORTED_AGENTS:
            raise ConfigurationError(f"unsupported target agent: {target.agent!r}")
        if target.scope not in {"user", "project"}:
            raise ConfigurationError(f"unsupported installation scope: {target.scope!r}")
        if target.scope == "project" and target.project_root is None:
            raise ConfigurationError(f"{target.profile}: project scope requires explicit project_root")
        entry = target.resource.path.resolve(strict=True)
        if not entry.is_file() or entry.name != "SKILL.md":
            raise ConfigurationError(f"{target.resource.ref}: missing skill entrypoint: {entry}")
        project = target.project_root if target.scope == "project" else None
        if project is not None:
            project = project.resolve(strict=True)
            if not project.is_dir():
                raise ConfigurationError(f"project_root is not a directory: {project}")
        plans.append(SkillPlan(target.resource.ref, target.resource.name, entry.parent,
                               target.profile, target.agent, target.scope, project))
    return tuple(plans)


def provision_skills(plans, *, home: Path | None = None,
                     registry: Path | None = None) -> ProvisionResult:
    """Keep successful actions and report failures without deleting shared skills.

    Inspection can be indeterminate when native plugin inventory is unavailable.
    In that case ZuAT's non-forced install still performs its locked preflight;
    inspection alone never grants permission to overwrite a target.
    """
    outcomes = []
    for plan in plans:
        context = dict(root=registry, home=home, project_root=plan.project_root)
        try:
            observed = inspect_asset(plan.asset(), **context)
            if observed.classification == "current" and observed.owned and observed.source_matches:
                outcomes.append(SkillOutcome(plan.ref, "reused", plan))
                continue
            if observed.classification in {"unsupported", "unowned", "conflict"}:
                outcomes.append(SkillOutcome(plan.ref, "failed", plan,
                    observed.diagnostics or (f"native target is {observed.classification}",)))
                continue
            if observed.classification == "indeterminate":
                # ZuAT install may adopt identical foreign bytes. An unresolved
                # ownership check must not turn that into implicit adoption.
                cwd = plan.project_root or home or Path.home()
                located = locate_skill(plan.agent, plan.name, cwd=cwd, home=home)
                copies = [locate_skill(plan.agent, plan.name, cwd=cwd, home=home,
                                      selected=item.path) for item in located.candidates]
                if (located.outcome not in {"missing", "located", "unresolved"}
                        or any(item.scope == plan.scope or item.outcome != "located" for item in copies)
                        or (located.outcome != "missing" and not copies)):
                    outcomes.append(SkillOutcome(plan.ref, "failed", plan,
                        observed.diagnostics or ("native ownership could not be verified",)))
                    continue
            result = install(ZuatRequest(agents=(plan.agent,), assets=(plan.asset(),)), **context)
            outcomes.append(SkillOutcome(plan.ref, "installed" if result.ok else "failed", plan,
                tuple(result.diagnostics) or (() if result.ok else (f"ZuAT returned {result.status}",)),
                result.operation_id))
        except (OSError, ValueError) as error:
            outcomes.append(SkillOutcome(plan.ref, "failed", plan, (str(error),)))
    return ProvisionResult(tuple(outcomes))

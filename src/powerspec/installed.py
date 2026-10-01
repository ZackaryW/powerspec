"""Read-only bridge to native agent skill selection through ZuAT."""
from dataclasses import dataclass
from pathlib import Path

from zuat.pub import locate_skill

from .catalog import ConfigurationError


@dataclass(frozen=True)
class InstalledSkill:
    root: Path
    entrypoint: Path
    scope: str
    provenance: str | None


def installed_skill(agent: str, name: str, *, cwd: Path, home: Path | None = None,
                    selected: Path | None = None) -> InstalledSkill | None:
    """Locate the exact native copy without observing, registering, or writing."""
    result = locate_skill(agent, name, cwd=cwd, home=home, selected=selected)
    if result.outcome == "missing":
        details = "; ".join(result.diagnostics) or "no installed candidate"
        raise ConfigurationError(f"installed skill {name!r} is missing for {agent}: {details}")
    if result.outcome != "located":
        details = "; ".join(result.diagnostics) or result.outcome
        raise ConfigurationError(
            f"cannot resolve installed skill {name!r} for {agent} ({result.outcome}): {details}"
        )
    if result.root is None or result.entrypoint is None or result.scope is None:
        raise ConfigurationError(f"ZuAT returned an incomplete location for {name!r}")
    root = result.root.resolve(strict=True)
    entrypoint = result.entrypoint.resolve(strict=True)
    if not entrypoint.is_relative_to(root) or entrypoint.name != "SKILL.md":
        raise ConfigurationError(f"ZuAT returned an invalid entrypoint for {name!r}: {entrypoint}")
    return InstalledSkill(root, entrypoint, result.scope, result.provenance)

"""Plan and initialize the Git-root OpenSpec consumer without replacing values."""
from dataclasses import dataclass
from pathlib import Path
import json
import re
import shutil
import subprocess

from zuat.pub import SUPPORTED_AGENTS

from .catalog import ConfigurationError, read_toml, reference
from .consumer import find_git_root
from .models import ConsumerConfig
from .profiles import compose
from .provisioning import SkillPlan, ProvisionResult, plan_skills, provision_skills


@dataclass(frozen=True)
class InitializationPlan:
    root: Path
    config_path: Path
    profile: str | None
    skills: tuple[SkillPlan, ...]
    config_bytes: bytes | None


@dataclass(frozen=True)
class InitializationResult:
    root: Path
    provisioning: ProvisionResult
    warnings: tuple[str, ...]


def _contained(root, relative):
    path = root / relative
    if not path.resolve().is_relative_to(root):
        raise ConfigurationError(f"initialization path escapes Git root: {path}")
    return path


def plan_initialization(cwd: Path, *, agent: str | None, catalog, profile=None):
    if agent not in SUPPORTED_AGENTS:
        raise ConfigurationError("init requires an explicit supported --agent: " + ", ".join(SUPPORTED_AGENTS))
    root = find_git_root(cwd)
    if root is None:
        raise ConfigurationError("init requires an existing Git repository")
    config_path = _contained(root, "openspec/.pspec/config.toml")
    original = config_path.read_bytes() if config_path.exists() else None
    config = ConsumerConfig.model_validate(read_toml(config_path)) if original is not None else ConsumerConfig()
    if profile:
        reference(profile)
        if original is not None and "profile" in read_toml(config_path) and config.profile is None:
            raise ConfigurationError("config.toml explicitly sets an empty profile; edit it to select another profile")
        if config.profile is not None and config.profile != profile:
            raise ConfigurationError(f"{config_path}: profile already selects {config.profile}; edit config.toml to change it")
    selected = config.profile or profile or None
    bundle = compose(catalog, selected, agent=agent, project_root=root,
                     exclude_profiles=config.exclude_profiles)
    return InitializationPlan(root, config_path, selected, plan_skills(bundle), original)


def bootstrap_openspec(root: Path):
    executable = shutil.which("openspec")
    if executable is None:
        raise ConfigurationError("OpenSpec CLI is required for initialization; install compatible OpenSpec 1.13.2 or later")
    try:
        version = subprocess.run([executable, "--version"], capture_output=True, text=True,
                                 cwd=root, timeout=15)
        match = re.search(r"\b(\d+)\.(\d+)\.(\d+)\b", version.stdout)
        if version.returncode or not match:
            raise ConfigurationError("cannot determine installed OpenSpec CLI version")
        if tuple(map(int, match.groups())) < (1, 13, 2):
            raise ConfigurationError(f"OpenSpec {match.group()} is older than bundled skill compatibility (1.13.2)")
        result = subprocess.run([executable, "init", str(root), "--tools", "none", "--no-animation"],
                                cwd=root, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ConfigurationError(f"OpenSpec bootstrap failed: {error}") from error
    if result.returncode:
        raise ConfigurationError(f"OpenSpec bootstrap failed: {result.stderr.strip() or result.stdout.strip()}")
    if not (root / "openspec/config.yaml").is_file():
        raise ConfigurationError("OpenSpec bootstrap did not create openspec/config.yaml")


def initialize(plan: InitializationPlan, *, home=None, registry=None) -> InitializationResult:
    root = plan.root
    for name in ("openspec/config.yaml", "openspec/.pspec/config.toml",
                 "openspec/.pspec/current.toml", "openspec/.pspec/.gitignore",
                 "openspec/specs", "openspec/changes"):
        _contained(root, name)
    observed = plan.config_path.read_bytes() if plan.config_path.exists() else None
    if observed != plan.config_bytes:
        raise ConfigurationError("consumer configuration changed after initialization planning; rerun init")
    target = root / "openspec/config.yaml"
    if not target.exists():
        bootstrap_openspec(root)
    elif not target.is_file():
        raise ConfigurationError(f"OpenSpec config is not a file: {target}")
    for relative in ("openspec/specs", "openspec/changes", "openspec/.pspec"):
        (root / relative).mkdir(parents=True, exist_ok=True)
    if plan.config_bytes is None:
        with plan.config_path.open("x", encoding="utf-8") as stream:
            selection = f"profile = {json.dumps(plan.profile)}\n\n" if plan.profile else ""
            stream.write(selection + "[vars]\n")
    elif plan.profile and ConsumerConfig.model_validate(read_toml(plan.config_path)).profile is None:
        # Put the new top-level key before any existing variable tables.
        plan.config_path.write_bytes(f"profile = {json.dumps(plan.profile)}\n".encode() + plan.config_bytes)
    current = plan.config_path.parent / "current.toml"
    if not current.exists():
        with current.open("x", encoding="utf-8") as stream:
            stream.write("[vars]\n")
    ignore = plan.config_path.parent / ".gitignore"
    existing = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
    if not existing.splitlines() or existing.splitlines()[-1] != "/current.toml":
        with ignore.open("a", encoding="utf-8") as stream:
            stream.write(("\n" if existing and not existing.endswith("\n") else "") + "/current.toml\n")
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", "openspec/.pspec/current.toml"],
                             cwd=root, capture_output=True, timeout=15)
    warnings = ("current.toml is already tracked; adding an ignore rule does not untrack it",) if tracked.returncode == 0 else ()
    return InitializationResult(root, provision_skills(plan.skills, home=home, registry=registry), warnings)

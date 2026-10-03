"""Workset policy: pure preflight plans followed by explicit Git effects."""
from dataclasses import dataclass
from pathlib import Path
import re

from .utils.git_worktrees import (RepositoryInfo, inspect_repository, list_worktrees,
    validate_branch, branch_exists, resolve_commit, add_worktree)
from .utils.git_worktrees import git_bytes
from .utils.tree_copy import assert_plain_path
from .workset_openspec import Member, Workset, validate_name


def parse_overrides(tokens: list[str]) -> dict[int, dict[str, str]]:
    result = {}
    index = 0
    while index < len(tokens):
        flag, equals, value = tokens[index].partition("=")
        match = re.fullmatch(r"--(repo|branch|remote|worktree)([1-9][0-9]*)", flag)
        if not match:
            raise ValueError(f"Unknown indexed option: {flag}")
        if not equals:
            index += 1
            if index >= len(tokens) or tokens[index].startswith("--"):
                raise ValueError(f"Missing value for {flag}")
            value = tokens[index]
        if not value:
            raise ValueError(f"Missing value for {flag}")
        field, number = match[1], int(match[2])
        group = result.setdefault(number, {})
        if field in group:
            raise ValueError(f"Duplicate option: {flag}")
        group[field] = value
        index += 1
    for number, group in result.items():
        if "repo" not in group:
            raise ValueError(f"--repo{number} is required for its overrides")
    return result


def branch_token(branch: str) -> str:
    value = re.sub(r"[^a-z0-9-]+", "-", branch.lower()).strip("-")
    if not value:
        raise ValueError(f"Branch has no usable directory token: {branch!r}")
    return value


def directory_name(name: str) -> str:
    if (not name or name in (".", "..") or name[-1] in " ." or
        re.search(r'[<>:"/\\|?*\x00-\x1f]', name) or
        re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³])(?:\..*)?", name)):
        raise ValueError(f"Unsafe worktree directory name: {name!r}")
    return name


@dataclass(frozen=True)
class RepositoryPlan:
    label: str
    repository: RepositoryInfo
    branch: str
    destination: Path
    base: str | None
    create_branch: bool
    reuse: bool


@dataclass(frozen=True)
class LaunchPlan:
    source: Workset
    name: str
    repositories: tuple[RepositoryPlan, ...]

    @property
    def output(self):
        return Workset(self.name, tuple(Member(p.label, p.destination) for p in self.repositories), self.source.tool)


def add_source(adapter, name: str, path: Path) -> dict:
    validate_name(name)
    repository = inspect_repository(path)
    existing = adapter.list_worksets().get(name)
    if existing:
        for member in existing.members:
            if inspect_repository(member.path).common_dir == repository.common_dir:
                return {"name": name, "action": "reused", "path": repository.root}
        if any(m.name == repository.root.name for m in existing.members):
            raise ValueError(f"Member label conflict: {repository.root.name}")
        action = adapter.append_member(existing, Member(repository.root.name, repository.root))
        return {"name": name, "action": action, "path": repository.root}
    action = adapter.publish(Workset(name, (Member(repository.root.name, repository.root),)))
    return {"name": name, "action": action, "path": repository.root}


def plan_launch(adapter, source_name: str, branch: str, overrides: dict,
                *, name: str | None = None) -> LaunchPlan:
    worksets = adapter.list_worksets()
    if source_name not in worksets:
        raise ValueError(f"Unknown source workset: {source_name}")
    source = worksets[source_name]
    output_name = name or f"{source_name}-{branch_token(branch)}"
    validate_name(output_name)
    if output_name == source_name:
        raise ValueError("Output workset must differ from the source")
    labels = {m.name for m in source.members}
    selections = {}
    for group in overrides.values():
        label = group["repo"]
        if label not in labels:
            raise ValueError(f"Unknown source member: {label}")
        if label in selections:
            raise ValueError(f"Repeated member selector: {label}")
        selections[label] = {k: v for k, v in group.items() if k != "repo"}
    identities = {}
    errors = []
    for member in source.members:
        try:
            info = inspect_repository(member.path)
            if info.common_dir not in identities:
                identities[info.common_dir] = (member.name, info, {})
            options = identities[info.common_dir][2]
            for key, value in selections.get(member.name, {}).items():
                if key in options and options[key] != value:
                    raise ValueError(f"Conflicting aliases for {info.original}: {key}")
                options[key] = value
        except (ValueError, OSError) as error:
            errors.append(f"{member.name}: {error}")
    plans = []
    paths = set()
    for label, info, options in identities.values():
        try:
            target_branch = options.get("branch", branch)
            validate_branch(info.root, target_branch)
            if "remote" in options:
                if "/" not in options["remote"]:
                    raise ValueError("Remote base must name a remote-tracking branch, such as origin/main")
                git_bytes(info.root, "check-ref-format", "refs/remotes/" + options["remote"])
            component = directory_name(options.get("worktree", f"{info.original.name}-{branch_token(target_branch)}"))
            destination = info.original.parent / component
            assert_plain_path(destination)
            destination = destination.resolve()
            if destination == info.original or destination == info.root:
                raise ValueError("Source checkout cannot be an implementation worktree")
            if destination in paths:
                raise ValueError(f"Destination normalization collision: {destination}")
            paths.add(destination)
            inventory = list_worktrees(info.root)
            at_path = next((w for w in inventory if w.path == destination), None)
            reuse = False
            if at_path:
                if at_path.branch != target_branch or at_path.prunable or not destination.is_dir():
                    raise ValueError(f"Conflicting worktree at {destination}")
                actual = inspect_repository(destination)
                if actual.common_dir != info.common_dir:
                    raise ValueError(f"Wrong repository at {destination}")
                reuse = True
            elif destination.exists():
                raise ValueError(f"Destination already exists: {destination}")
            occupied = next((w for w in inventory if w.branch == target_branch and w.path != destination), None)
            if occupied:
                raise ValueError(f"Branch {target_branch} is occupied at {occupied.path}")
            exists = branch_exists(info.root, target_branch)
            base = None
            if not reuse:
                if exists and "remote" in options:
                    raise ValueError("Remote override cannot replace an existing branch")
                if not exists:
                    ref = "refs/remotes/" + options["remote"] if "remote" in options else "refs/heads/main"
                    base = resolve_commit(info.root, ref)
            plans.append(RepositoryPlan(label, info, target_branch, destination, base, not exists, reuse))
        except (ValueError, OSError) as error:
            errors.append(f"{label}: {error}")
    plan = LaunchPlan(source, output_name, tuple(plans))
    existing = worksets.get(output_name)
    if existing and existing.members != plan.output.members:
        errors.append(f"Output workset {output_name} has conflicting membership")
    if errors:
        raise ValueError("Launch preflight failed:\n" + "\n".join(errors))
    return plan


def execute_repositories(plan: LaunchPlan, outcomes: list | None = None) -> list:
    outcomes = [] if outcomes is None else outcomes
    for item in plan.repositories:
        assert_plain_path(item.destination)
        inventory = list_worktrees(item.repository.root)
        matched = next((w for w in inventory if w.path == item.destination), None)
        if matched:
            if matched.branch != item.branch or matched.prunable or inspect_repository(item.destination).common_dir != item.repository.common_dir:
                raise ValueError(f"Worktree changed after preflight: {item.destination}")
            action = "reused"
        else:
            if item.reuse or item.destination.exists() or branch_exists(item.repository.root, item.branch) == item.create_branch:
                raise ValueError(f"Worktree or branch changed after preflight: {item.destination}")
            try:
                add_worktree(item.repository.root, item.destination, branch=item.branch,
                             start_commit=item.base, create_branch=item.create_branch)
            except (ValueError, OSError):
                outcomes.append({"label": item.label, "path": item.destination, "branch": item.branch,
                                 "action": "failed", "observed": list_worktrees(item.repository.root)})
                raise
            action = "created"
        outcomes.append({"label": item.label, "path": item.destination, "branch": item.branch, "action": action, "base": item.base})
    return outcomes

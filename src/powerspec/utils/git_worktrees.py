"""Native Git worktree mechanics, independent of project configuration policy."""
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess


class GitError(ValueError):
    """Git could not complete an operation; mutations may have partial effects."""


def git_bytes(root: Path, *args: str, timeout: float = 30) -> bytes:
    """Execute literal Git arguments with a timeout and preserve byte output."""
    env = dict(os.environ)
    # An inherited Git context must not redirect an operation to another repo.
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
        env.pop(key, None)
    try:
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                                env=env, timeout=timeout, shell=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GitError(f"Git operation failed in {root}: {error}") from error
    if result.returncode:
        raise GitError(f"Git in {root}: {os.fsdecode(result.stderr).strip()}")
    return result.stdout


def git_text(root: Path, *args: str, timeout: float = 30) -> str:
    return os.fsdecode(git_bytes(root, *args, timeout=timeout)).rstrip("\r\n")


@dataclass(frozen=True)
class WorktreeInfo:
    path: Path
    commit: str
    branch: str | None
    locked: bool = False
    prunable: bool = False
    detached: bool = False


@dataclass(frozen=True)
class RepositoryInfo:
    root: Path
    original: Path
    common_dir: Path
    git_dir: Path
    commit: str


def list_worktrees(repository: Path, *, timeout: float = 30) -> tuple[WorktreeInfo, ...]:
    """Read Git's NUL-delimited inventory, including unavailable registrations."""
    raw = git_bytes(repository, "worktree", "list", "--porcelain", "-z", timeout=timeout)
    items = []
    for block in raw.split(b"\0\0"):
        if not block.strip(b"\0"):
            continue
        fields = {}
        for line in block.split(b"\0"):
            key, _, value = line.partition(b" ")
            fields[os.fsdecode(key)] = os.fsdecode(value)
        if "worktree" not in fields or "HEAD" not in fields:
            raise GitError("Malformed Git worktree inventory")
        branch = fields.get("branch")
        items.append(WorktreeInfo(Path(fields["worktree"]).resolve(), fields["HEAD"],
                     branch.removeprefix("refs/heads/") if branch else None,
                     "locked" in fields, "prunable" in fields, "detached" in fields))
    return tuple(items)


def inspect_repository(path: Path, *, timeout: float = 30) -> RepositoryInfo:
    """Resolve a non-bare, committed checkout, including linked worktrees."""
    path = Path(path).resolve(strict=True)
    if git_text(path, "rev-parse", "--is-bare-repository", timeout=timeout) != "false":
        raise GitError(f"Bare repository is not a checkout: {path}")
    root = Path(git_text(path, "rev-parse", "--show-toplevel", timeout=timeout)).resolve()
    common = Path(git_text(root, "rev-parse", "--path-format=absolute", "--git-common-dir", timeout=timeout)).resolve()
    administrative = Path(git_text(root, "rev-parse", "--absolute-git-dir", timeout=timeout)).resolve()
    commit = resolve_commit(root, "HEAD", timeout=timeout)
    inventory = list_worktrees(root, timeout=timeout)
    if not inventory:
        raise GitError(f"No original checkout for {path}")
    return RepositoryInfo(root, inventory[0].path, common, administrative, commit)


def validate_branch(repository: Path, branch: str) -> None:
    if not branch or branch.startswith("-") or branch == "HEAD":
        raise GitError(f"Invalid branch: {branch!r}")
    git_bytes(repository, "check-ref-format", "refs/heads/" + branch)


def resolve_commit(repository: Path, ref: str, *, timeout: float = 30) -> str:
    return git_text(repository, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}", timeout=timeout)


def branch_exists(repository: Path, branch: str) -> bool:
    # --verify on rev-parse returns 128 for a missing reference; inventory avoids
    # hiding other Git errors as an absent branch.
    refs = git_text(repository, "for-each-ref", "--format=%(refname)", "refs/heads/").splitlines()
    return "refs/heads/" + branch in refs


def add_worktree(repository: Path, destination: Path, *, branch: str,
                 start_commit: str | None, create_branch: bool, timeout: float = 60) -> WorktreeInfo:
    """Create through Git without resetting refs, forcing checkout, or rollback."""
    validate_branch(repository, branch)
    args = ["worktree", "add"]
    if create_branch:
        if start_commit is None:
            raise GitError("Creating a branch requires an explicit starting commit")
        args += ["-b", branch]
    args += ["--", str(destination), start_commit if create_branch else branch]
    git_bytes(repository, *args, timeout=timeout)
    for entry in list_worktrees(repository):
        if entry.path == destination.resolve() and entry.branch == branch and not entry.prunable:
            return entry
    raise GitError(f"Created worktree could not be verified: {destination}")

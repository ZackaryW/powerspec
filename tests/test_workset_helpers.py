import shutil
import subprocess
from pathlib import Path

import pytest


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True).stdout.decode().strip()


def repo(path):
    path.mkdir()
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "core.autocrlf", "false")
    git(path, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-qm", "base")
    return path


def test_inspect_linked_checkout_and_preserve_source(tmp_path):
    from powerspec.utils.git_worktrees import inspect_repository, add_worktree, list_worktrees
    source = repo(tmp_path / "source repo")
    (source / "dirty.txt").write_text("keep")
    before = git(source, "rev-parse", "HEAD")
    target = tmp_path / "target work"
    created = add_worktree(source, target, branch="feature/one", start_commit=before, create_branch=True)
    assert created.branch == "feature/one"
    nested = target / "nested"
    nested.mkdir()
    info = inspect_repository(nested)
    assert info.root == target.resolve()
    assert info.original == source.resolve()
    assert info.common_dir == inspect_repository(source).common_dir
    assert len(list_worktrees(source)) == 2
    assert git(source, "branch", "--show-current") == "main"
    assert (source / "dirty.txt").read_text() == "keep"
    assert not (target / "dirty.txt").exists()


def test_existing_branch_conflict_and_prunable_inventory(tmp_path):
    from powerspec.utils.git_worktrees import add_worktree, list_worktrees, GitError
    source = repo(tmp_path / "source")
    git(source, "branch", "existing")
    target = tmp_path / "target"
    add_worktree(source, target, branch="existing", start_commit=None, create_branch=False)
    with pytest.raises(GitError):
        add_worktree(source, tmp_path / "other", branch="existing", start_commit=None, create_branch=False)
    # Disposable fixture only: simulate an externally removed worktree.
    shutil.rmtree(target)
    assert any(w.prunable for w in list_worktrees(source))


def test_invalid_and_unborn_repository(tmp_path):
    from powerspec.utils.git_worktrees import inspect_repository, GitError
    with pytest.raises(GitError):
        inspect_repository(tmp_path)
    git(tmp_path, "init", "-q")
    with pytest.raises(GitError):
        inspect_repository(tmp_path)


def test_verified_tree_copy_and_conflicts(tmp_path):
    from powerspec.utils.tree_copy import snapshot_tree, copy_verified_tree, TreeError
    source = tmp_path / "source"
    (source / "nested").mkdir(parents=True)
    (source / "empty").mkdir()
    (source / "nested/file").write_bytes(b"data\r\n")
    snap = snapshot_tree(source)
    target = tmp_path / "target"
    assert copy_verified_tree(source, target, snap) is True
    assert snapshot_tree(target) == snap
    assert copy_verified_tree(source, target, snap) is False
    (target / "nested/file").write_text("different")
    with pytest.raises(TreeError, match="different"):
        copy_verified_tree(source, target, snap)
    (source / "new").write_text("changed")
    with pytest.raises(TreeError, match="changed"):
        copy_verified_tree(source, tmp_path / "another", snap)
    assert not (tmp_path / "another").exists()


def test_tree_rejects_links(tmp_path):
    from powerspec.utils.tree_copy import snapshot_tree, TreeError
    source = tmp_path / "source"
    source.mkdir()
    try:
        (source / "link").symlink_to(tmp_path, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(TreeError, match="link"):
        snapshot_tree(source)


def test_detached_inventory_and_exact_base(tmp_path):
    from powerspec.utils.git_worktrees import list_worktrees, resolve_commit, add_worktree, validate_branch, GitError
    source = repo(tmp_path / "source")
    base = resolve_commit(source, "main")
    git(source, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-qm", "second")
    git(source, "worktree", "add", "--detach", str(tmp_path / "detached"), base)
    assert list_worktrees(source)[1].detached
    result = add_worktree(source, tmp_path / "old base", branch="old", start_commit=base, create_branch=True)
    assert result.commit == base
    with pytest.raises(GitError):
        validate_branch(source, "@{-1}")


def test_git_timeout_has_context(tmp_path, monkeypatch):
    from powerspec.utils.git_worktrees import git_bytes, GitError
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])
    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(GitError, match="Git operation failed"):
        git_bytes(tmp_path, "status", timeout=.1)


@pytest.mark.parametrize("interrupt", [False, True])
def test_copy_interruption_or_source_race_preserves_destination(tmp_path, monkeypatch, interrupt):
    from powerspec.utils.tree_copy import snapshot_tree, copy_verified_tree, TreeError
    source = tmp_path / "source"
    source.mkdir()
    (source / "file").write_text("first")
    snap = snapshot_tree(source)
    original = shutil.copytree
    def racing_copy(*args, **kwargs):
        result = original(*args, **kwargs)
        if interrupt:
            raise OSError("interrupted")
        (source / "file").write_text("second")
        return result
    monkeypatch.setattr(shutil, "copytree", racing_copy)
    with pytest.raises((TreeError, OSError)):
        copy_verified_tree(source, tmp_path / "target", snap)
    assert not (tmp_path / "target").exists()
    assert not list(tmp_path.glob(".pspec-copy-*"))

from pathlib import Path

from test_workset_helpers import git, repo
from test_workset_launch import Registry
import pytest


def test_projected_tree_uses_checkout_line_endings(tmp_path):
    from powerspec.worksets import plan_launch
    from powerspec.workset_openspec import Member
    from powerspec.workset_stores import TargetView
    source = repo(tmp_path / "source")
    git(source, "config", "core.autocrlf", "true")
    (source / "file.md").write_bytes(b"line\r\n")
    git(source, "add", "file.md")
    git(source, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")
    plan = plan_launch(Registry([Member("x", source)]), "base", "topic", {})
    assert TargetView(plan.repositories[0]).read(Path("file.md")) == b"line\r\n"


def test_store_preflight_reports_independent_collisions_together(tmp_path):
    from powerspec.worksets import plan_launch
    from powerspec.workset_openspec import Member
    from powerspec.workset_stores import plan_stores
    first, second = repo(tmp_path / "first"), repo(tmp_path / "second")
    registry = Registry([Member("first", first), Member("second", second)])
    registry.list_stores = lambda: {"first": first, "second": second, "first-topic": tmp_path / "one", "second-topic": tmp_path / "two"}
    plan = plan_launch(registry, "base", "topic", {})
    with pytest.raises(ValueError) as error:
        plan_stores(registry, plan)
    assert "first-topic" in str(error.value) and "second-topic" in str(error.value)

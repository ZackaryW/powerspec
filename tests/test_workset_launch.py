import pytest

from test_workset_helpers import git, repo


def test_indexed_flags_are_strict():
    from powerspec.worksets import parse_overrides
    assert parse_overrides(["--repo999=x", "--branch999", "feature/x"]) == {999: {"repo": "x", "branch": "feature/x"}}
    for args in (["--repo0=x"], ["--wat=x"], ["--branch2=x"], ["--repo1=x", "--repo1=y"], ["--repo1"]):
        with pytest.raises(ValueError):
            parse_overrides(args)


class Registry:
    def __init__(self, members):
        from powerspec.workset_openspec import Workset
        self.worksets = {"base": Workset("base", tuple(members), None)}
    def list_worksets(self):
        return self.worksets
    def publish(self, workset):
        self.worksets[workset.name] = workset


def test_launch_dirty_source_dedup_and_repeat(tmp_path):
    from powerspec.worksets import plan_launch, execute_repositories
    from powerspec.workset_openspec import Member
    source = repo(tmp_path / "source")
    nested = source / "nested"
    nested.mkdir()
    (source / "dirty").write_text("keep")
    adapter = Registry([Member("first", source), Member("alias", nested)])
    plan = plan_launch(adapter, "base", "feature/A", {})
    assert len(plan.repositories) == 1
    assert plan.name == "base-feature-a"
    results = execute_repositories(plan)
    assert results[0]["action"] == "created"
    target = tmp_path / "source-feature-a"
    assert git(target, "branch", "--show-current") == "feature/A"
    (target / "local").write_text("preserve")
    retry = plan_launch(adapter, "base", "feature/A", {1: {"repo": "first", "remote": "missing/ref"}})
    assert execute_repositories(retry)[0]["action"] == "reused"
    assert (source / "dirty").read_text() == "keep"


def test_preflight_aggregates_and_has_no_effects(tmp_path):
    from powerspec.worksets import plan_launch
    from powerspec.workset_openspec import Member
    source = repo(tmp_path / "source")
    adapter = Registry([Member("ok", source), Member("bad", tmp_path / "absent")])
    with pytest.raises(ValueError, match="bad"):
        plan_launch(adapter, "base", "feature", {})
    assert not (tmp_path / "source-feature").exists()
    assert git(source, "branch", "--list", "feature") == ""


def test_alias_conflicts_and_remote_base(tmp_path):
    from powerspec.worksets import plan_launch, execute_repositories
    from powerspec.workset_openspec import Member
    source = repo(tmp_path / "source")
    git(source, "update-ref", "refs/remotes/origin/topic", "HEAD")
    adapter = Registry([Member("x", source), Member("y", source)])
    with pytest.raises(ValueError, match="aliases"):
        plan_launch(adapter, "base", "a", {1: {"repo": "x", "branch": "b"}, 3: {"repo": "y", "branch": "c"}})
    plan = plan_launch(adapter, "base", "a", {1: {"repo": "x", "remote": "origin/topic"}})
    execute_repositories(plan)
    assert git(tmp_path / "source-a", "rev-parse", "HEAD") == git(source, "rev-parse", "refs/remotes/origin/topic")


def test_adapter_real_isolated_registry(tmp_path, monkeypatch):
    from powerspec.workset_openspec import OpenSpec, Member, Workset
    from powerspec.worksets import add_source
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    source = repo(tmp_path / "source")
    adapter = OpenSpec(tmp_path)
    assert add_source(adapter, "demo", source)["action"] == "created"
    assert add_source(adapter, "demo", source)["action"] == "reused"
    other = repo(tmp_path / "other")
    with pytest.raises(ValueError, match="append"):
        add_source(adapter, "demo", other)
    assert adapter.list_worksets()["demo"].members == (Member("source", source),)
    adapter.publish(Workset("copy", (Member("source", source),), None))
    adapter.publish(Workset("copy", (Member("source", source),), None))
    with pytest.raises(ValueError, match="membership"):
        adapter.publish(Workset("copy", (Member("other", other),), None))


@pytest.mark.parametrize("option", [{"branch": "main"}, {"remote": "origin/missing"}, {"worktree": "../escape"}, {"worktree": "CON"}])
def test_planner_rejects_conflicts_before_effects(tmp_path, option):
    from powerspec.worksets import plan_launch
    from powerspec.workset_openspec import Member
    source = repo(tmp_path / "source")
    with pytest.raises(ValueError):
        plan_launch(Registry([Member("x", source)]), "base", "topic", {1: {"repo": "x", **option}})
    assert git(source, "branch", "--list", "topic") == ""


def test_partial_creation_and_retry(tmp_path, monkeypatch):
    import powerspec.worksets as module
    from powerspec.workset_openspec import Member
    first, second = repo(tmp_path / "first"), repo(tmp_path / "second")
    adapter = Registry([Member("a", first), Member("b", second)])
    plan = module.plan_launch(adapter, "base", "topic", {})
    original = module.add_worktree
    def fail_second(root, *args, **kwargs):
        if root == second:
            raise ValueError("injected second failure")
        return original(root, *args, **kwargs)
    monkeypatch.setattr(module, "add_worktree", fail_second)
    outcomes = []
    with pytest.raises(ValueError, match="second failure"):
        module.execute_repositories(plan, outcomes)
    assert [o["action"] for o in outcomes] == ["created", "failed"]
    monkeypatch.setattr(module, "add_worktree", original)
    retry = module.plan_launch(adapter, "base", "topic", {})
    assert [o["action"] for o in module.execute_repositories(retry)] == ["reused", "created"]


def test_concurrent_branch_creation_is_not_adopted(tmp_path):
    from powerspec.worksets import plan_launch, execute_repositories
    from powerspec.workset_openspec import Member
    source = repo(tmp_path / "source")
    plan = plan_launch(Registry([Member("x", source)]), "base", "topic", {})
    git(source, "branch", "topic")
    with pytest.raises(ValueError, match="changed after preflight"):
        execute_repositories(plan)
    assert not (tmp_path / "source-topic").exists()


def test_adapter_rejects_malformed_output_and_missing_prerequisite(tmp_path, monkeypatch):
    from powerspec.workset_openspec import OpenSpec
    adapter = OpenSpec(tmp_path, env={"PATH": ""})
    with pytest.raises(ValueError, match="required"):
        adapter.list_worksets()
    monkeypatch.setattr(adapter, "call", lambda *a: {"worksets": [{"name": "x", "members": "bad"}]})
    with pytest.raises(ValueError, match="Malformed"):
        adapter.list_worksets()

import json
from pathlib import Path

import pytest

from test_workset_helpers import git, repo


def planning_root(path):
    (path / "openspec/changes").mkdir(parents=True, exist_ok=True)
    (path / "openspec/specs").mkdir(parents=True, exist_ok=True)
    (path / "openspec/config.yaml").write_text("schema: spec-driven\n")
    (path / "openspec/specs/.gitkeep").touch()
    (path / "openspec/changes/.gitkeep").touch()


def change(root, name="feature"):
    target = root / "openspec/changes" / name
    target.mkdir()
    (target / ".openspec.yaml").write_text("schema: spec-driven\n")
    (target / "proposal.md").write_text("# Proposal\nCurrent uncommitted text\n")
    return target


def commit(root):
    git(root, "add", ".")
    git(root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")


@pytest.fixture
def adapter(tmp_path, monkeypatch):
    from powerspec.workset_openspec import OpenSpec
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "global-config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "global-data"))
    return OpenSpec(tmp_path)


def test_real_store_move_and_completed_retry(tmp_path, adapter):
    from powerspec.workset_openspec import Member, Workset
    from powerspec.workset_launch import launch
    source = repo(tmp_path / "source")
    planning_root(source)
    adapter.register_store(source, "specs")
    commit(source)
    selected = change(source)
    adapter.publish(Workset("base", (Member("specs", source),)))
    result = launch(adapter, "base", "topic", {}, change="feature")
    assert result["ok"], result
    target = tmp_path / "source-topic"
    assert not selected.exists()
    assert (target / "openspec/changes/feature/proposal.md").read_text().endswith("uncommitted text\n")
    assert adapter.list_stores() == {"specs": source, "specs-topic": target}
    assert "id: specs\n" in (source / ".openspec-store/store.yaml").read_text()
    assert "id: specs-topic\n" in (target / ".openspec-store/store.yaml").read_text()
    (target / "openspec/changes/feature/proposal.md").write_text("later implementation")
    retry = launch(adapter, "base", "topic", {}, change="feature")
    assert retry["ok"], retry
    assert retry["transfer"]["action"] == "already-moved"


def test_ambiguous_owner_and_keep_source(tmp_path, adapter):
    from powerspec.workset_openspec import Member, Workset
    from powerspec.workset_launch import launch
    sources = [repo(tmp_path / label) for label in ("first", "second")]
    for index, source in enumerate(sources):
        planning_root(source)
        adapter.register_store(source, f"specs-{index}")
        commit(source)
        change(source)
    adapter.publish(Workset("base", tuple(Member(p.name, p) for p in sources)))
    failed = launch(adapter, "base", "topic", {}, change="feature")
    assert not failed["ok"] and "ambiguous" in failed["errors"][0].lower()
    assert not (tmp_path / "first-topic").exists()
    result = launch(adapter, "base", "topic", {}, change="feature", store="specs-1", keep_source=True)
    assert result["ok"], result
    assert all((p / "openspec/changes/feature").exists() for p in sources)
    assert not (tmp_path / "first-topic/openspec/changes/feature").exists()
    assert (tmp_path / "second-topic/openspec/changes/feature").is_dir()


def test_conflicting_inherited_change_fails_before_mutation(tmp_path, adapter):
    from powerspec.workset_openspec import Member, Workset
    from powerspec.workset_launch import launch
    source = repo(tmp_path / "source")
    planning_root(source)
    selected = change(source)
    commit(source)
    (selected / "proposal.md").write_text("new local version")
    adapter.publish(Workset("base", (Member("source", source),)))
    result = launch(adapter, "base", "topic", {}, change="feature")
    assert not result["ok"] and "different" in result["errors"][0]
    assert not (tmp_path / "source-topic").exists()


def test_nested_stores_and_pointer_routing(tmp_path, adapter):
    from powerspec.workset_openspec import Member, Workset
    from powerspec.workset_launch import launch
    source = repo(tmp_path / "source")
    nested = source / "planning"
    planning_root(nested)
    adapter.register_store(nested, "nested")
    (source / "openspec").mkdir()
    (source / "openspec/config.yaml").write_text("# preserve comment\nstore: nested\n")
    commit(source)
    change(nested)
    adapter.publish(Workset("base", (Member("code", source), Member("plans", nested))))
    result = launch(adapter, "base", "shared", {7: {"repo": "plans", "branch": "own"}}, name="custom", change="feature", keep_source=True)
    assert result["ok"], result
    target = tmp_path / "source-own"
    assert result["name"] == "custom"
    assert result["stores"][0]["id"] == "nested-own"
    assert (target / "openspec/config.yaml").read_text() == "# preserve comment\nstore: nested-own\n"
    assert adapter.call("list", cwd=target)["root"]["path"] == str(target / "planning")
    (target / "openspec/config.yaml").write_text("store: user-edited\n")
    retry = launch(adapter, "base", "shared", {7: {"repo": "plans", "branch": "own"}}, name="custom", change="feature", keep_source=True)
    assert not retry["ok"] and "Unexpected edited" in retry["errors"][0]
    assert (target / "openspec/config.yaml").read_text() == "store: user-edited\n"


def test_publication_failure_preserves_source_and_retry(tmp_path, adapter, monkeypatch):
    from powerspec.workset_openspec import Member, Workset
    from powerspec.workset_launch import launch
    source = repo(tmp_path / "source")
    planning_root(source)
    commit(source)
    selected = change(source)
    adapter.publish(Workset("base", (Member("source", source),)))
    publish = adapter.publish
    monkeypatch.setattr(adapter, "publish", lambda *a: (_ for _ in ()).throw(ValueError("publication failure")))
    result = launch(adapter, "base", "topic", {}, change="feature")
    assert not result["ok"] and result["stage"] == "publication"
    assert selected.is_dir()
    assert (tmp_path / "source-topic/openspec/changes/feature").is_dir()
    monkeypatch.setattr(adapter, "publish", publish)
    retry = launch(adapter, "base", "topic", {}, change="feature")
    assert retry["ok"], retry
    assert not selected.exists()


def test_partial_cleanup_retry_and_index_preservation(tmp_path, adapter, monkeypatch):
    from powerspec.workset_openspec import Member, Workset
    from powerspec.workset_launch import launch
    source = repo(tmp_path / "source")
    planning_root(source)
    selected = change(source)
    (selected / "z-extra.md").write_text("extra")
    commit(source)
    before_index = git(source, "ls-files", "--stage")
    adapter.publish(Workset("base", (Member("source", source),)))
    unlink = Path.unlink
    def fail(path, *args, **kwargs):
        if path == selected / "proposal.md":
            raise OSError("cleanup interruption")
        return unlink(path, *args, **kwargs)
    monkeypatch.setattr(Path, "unlink", fail)
    result = launch(adapter, "base", "topic", {}, change="feature")
    assert not result["ok"] and result["workspace_ready"] and result["stage"] == "cleanup", result
    assert result["transfer"]["action"] == "cleanup-incomplete"
    assert not (selected / "z-extra.md").exists()
    assert (selected / "proposal.md").exists()
    monkeypatch.setattr(Path, "unlink", unlink)
    retry = launch(adapter, "base", "topic", {}, change="feature")
    assert retry["ok"], retry
    assert not selected.exists()
    assert git(source, "ls-files", "--stage") == before_index


def test_source_mutation_before_cleanup_is_preserved(tmp_path, adapter, monkeypatch):
    from powerspec.workset_openspec import Member, Workset
    from powerspec.workset_launch import launch
    source = repo(tmp_path / "source")
    planning_root(source)
    commit(source)
    selected = change(source)
    adapter.publish(Workset("base", (Member("source", source),)))
    publish = adapter.publish
    def edit_then_publish(workset):
        (selected / "new.md").write_text("concurrent work")
        return publish(workset)
    monkeypatch.setattr(adapter, "publish", edit_then_publish)
    result = launch(adapter, "base", "topic", {}, change="feature")
    assert result["workspace_ready"] and not result["ok"]
    assert (selected / "new.md").read_text() == "concurrent work"
    assert (selected / "proposal.md").exists()


def test_invalid_receipt_and_destination_edits_preserved(tmp_path, adapter, monkeypatch):
    from powerspec.workset_openspec import Member, Workset
    from powerspec.workset_launch import launch
    from powerspec.utils.git_worktrees import inspect_repository
    source = repo(tmp_path / "source")
    planning_root(source)
    commit(source)
    selected = change(source)
    adapter.publish(Workset("base", (Member("source", source),)))
    publish = adapter.publish
    monkeypatch.setattr(adapter, "publish", lambda *a: (_ for _ in ()).throw(ValueError("publication failure")))
    assert launch(adapter, "base", "topic", {}, change="feature")["stage"] == "publication"
    target = tmp_path / "source-topic"
    receipt = next((inspect_repository(target).git_dir / "powerspec/transfers").glob("*.json"))
    original = receipt.read_bytes()
    payload = json.loads(original)
    payload["key"]["source"] = str(tmp_path / "outside")
    receipt.write_text(json.dumps(payload))
    monkeypatch.setattr(adapter, "publish", publish)
    invalid = launch(adapter, "base", "topic", {}, change="feature")
    assert not invalid["ok"] and "Invalid transfer receipt" in invalid["errors"][0]
    receipt.write_bytes(original)
    document = target / "openspec/changes/feature/proposal.md"
    document.write_text("destination edits")
    changed = launch(adapter, "base", "topic", {}, change="feature")
    assert not changed["ok"] and "different" in changed["errors"][0]
    assert selected.is_dir() and document.read_text() == "destination edits"


def test_absent_archived_and_external_store_are_not_candidates(tmp_path, adapter):
    from powerspec.workset_openspec import Member, Workset
    from powerspec.workset_launch import launch
    source = repo(tmp_path / "source")
    planning_root(source)
    (source / "openspec/changes/archive").mkdir()
    (source / "openspec/changes/archive/feature").mkdir()
    commit(source)
    adapter.publish(Workset("base", (Member("source", source),)))
    for options in ({}, {"store": "unrelated"}):
        result = launch(adapter, "base", "topic", {}, change="feature", **options)
        assert not result["ok"] and result["stage"] == "preflight"
    assert not (tmp_path / "source-topic").exists()


def test_store_collision_and_metadata_mismatch_preflight(tmp_path, adapter):
    from powerspec.workset_openspec import Member, Workset
    from powerspec.workset_launch import launch
    source, other = repo(tmp_path / "source"), repo(tmp_path / "other")
    for path in (source, other):
        planning_root(path)
    adapter.register_store(source, "specs")
    adapter.register_store(other, "specs-topic")
    commit(source)
    adapter.publish(Workset("base", (Member("source", source),)))
    result = launch(adapter, "base", "topic", {})
    assert not result["ok"] and "conflicts with registration" in result["errors"][0]
    assert not (tmp_path / "source-topic").exists()
    metadata = source / ".openspec-store/store.yaml"
    metadata.write_text("version: 1\nid: unexpected\n")
    mismatch = launch(adapter, "base", "other", {})
    assert not mismatch["ok"] and "identity mismatch" in mismatch["errors"][0]


def test_missing_destination_schema_preserves_source(tmp_path, adapter):
    from powerspec.workset_openspec import Member, Workset
    from powerspec.workset_launch import launch
    source = repo(tmp_path / "source")
    planning_root(source)
    commit(source)
    selected = change(source)
    # The schema is local uncommitted context, deliberately absent in the branch.
    schemas = source / "openspec/schemas/private"
    schemas.mkdir(parents=True)
    (schemas / "schema.yaml").write_text("name: private\nversion: 1\ndescription: fixture\nartifacts:\n  - id: proposal\n    generates: proposal.md\n    description: proposal\n    template: proposal.md\n    instruction: Write a proposal\n    requires: []\n")
    (schemas / "templates").mkdir()
    (schemas / "templates/proposal.md").write_text("# Proposal\n")
    (selected / ".openspec.yaml").write_text("schema: private\n")
    adapter.publish(Workset("base", (Member("source", source),)))
    result = launch(adapter, "base", "topic", {}, change="feature")
    assert not result["ok"], result
    assert result["stage"] == "transfer", result
    assert result["transfer"]["action"] == "copied-unverified"
    assert selected.is_dir() and not result["workspace_ready"]
    assert "base-topic" not in adapter.list_worksets()


def test_external_pointer_and_global_default_stay_external(tmp_path, adapter):
    from powerspec.workset_openspec import Member, Workset
    from powerspec.workset_launch import launch
    external, source = repo(tmp_path / "external"), repo(tmp_path / "source")
    planning_root(external)
    adapter.register_store(external, "external")
    change(external)
    global_config = Path(adapter.env["XDG_CONFIG_HOME"]) / "openspec/config.json"
    global_config.parent.mkdir(parents=True, exist_ok=True)
    global_config.write_text('{"defaultStore":"external"}\n')
    before = global_config.read_bytes()
    (source / "openspec").mkdir()
    (source / "openspec/config.yaml").write_text("store: external\n")
    commit(source)
    adapter.publish(Workset("base", (Member("code", source),)))
    rejected = launch(adapter, "base", "topic", {}, change="feature")
    assert not rejected["ok"] and "No active change" in rejected["errors"][0]
    assert not (tmp_path / "source-topic").exists()
    result = launch(adapter, "base", "topic", {})
    assert result["ok"] and not result["stores"], result
    assert (tmp_path / "source-topic/openspec/config.yaml").read_text() == "store: external\n"
    assert adapter.list_stores() == {"external": external}
    assert global_config.read_bytes() == before


def test_second_store_registration_failure_and_retry(tmp_path, adapter, monkeypatch):
    from powerspec.workset_openspec import Member, Workset
    from powerspec.workset_launch import launch
    sources = [repo(tmp_path / name) for name in ("first", "second")]
    for source in sources:
        planning_root(source)
        adapter.register_store(source, source.name)
        commit(source)
    selected = change(sources[0])
    adapter.publish(Workset("base", tuple(Member(p.name, p) for p in sources)))
    register = adapter.register_store
    def fail_second(root, identity):
        if identity == "second-topic":
            raise ValueError("second registration failure")
        return register(root, identity)
    monkeypatch.setattr(adapter, "register_store", fail_second)
    failed = launch(adapter, "base", "topic", {}, change="feature")
    assert not failed["ok"] and failed["stage"] == "stores"
    assert "first-topic" in adapter.list_stores() and "base-topic" not in adapter.list_worksets()
    assert selected.is_dir()
    assert any(e["action"] == "store-registration-failed" for e in failed["effects"])
    monkeypatch.setattr(adapter, "register_store", register)
    retry = launch(adapter, "base", "topic", {}, change="feature")
    assert retry["ok"], retry
    assert not selected.exists()

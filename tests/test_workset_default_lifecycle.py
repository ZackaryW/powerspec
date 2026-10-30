import pytest

from test_workset_helpers import repo
from powerspec.workset_defaults import load, normalize, record_for, store
from powerspec.workset_openspec import Member, Workset


@pytest.fixture
def adapter(tmp_path, monkeypatch):
    from powerspec.workset_openspec import OpenSpec
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "global-config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "global-data"))
    monkeypatch.setenv("OPENSPEC_TELEMETRY", "0")
    return OpenSpec(tmp_path)


@pytest.fixture
def defaults(tmp_path, monkeypatch):
    import powerspec.workset_defaults as module
    path = tmp_path / ".powerspec/worksets.toml"
    monkeypatch.setattr(module, "defaults_file", lambda: path)
    return path


def base(tmp_path, adapter, *labels):
    workset = Workset("base", tuple(Member(label, repo(tmp_path / label)) for label in labels))
    adapter.publish(workset)
    return workset


def test_launch_records_the_source_default_for_the_output(tmp_path, adapter, defaults):
    from powerspec.workset_launch import launch
    source = base(tmp_path, adapter, "central", "server")
    store(defaults, {"base": record_for(source, "central")})

    result = launch(adapter, "base", "feature-x", {})

    assert result["ok"], result
    assert result["default"] == {"action": "recorded", "label": "central"}
    entry = load(defaults)["base-feature-x"]
    assert normalize(entry.path) == normalize(tmp_path / "central-feature-x")
    assert {normalize(item) for item in entry.members} == {
        normalize(tmp_path / "central-feature-x"), normalize(tmp_path / "server-feature-x")}
    assert launch(adapter, "base", "feature-x", {})["default"] == {"action": "reused", "label": "central"}


def test_launch_keeps_a_different_existing_output_default(tmp_path, adapter, defaults):
    from powerspec.workset_launch import launch
    source = base(tmp_path, adapter, "central", "server")
    store(defaults, {"base": record_for(source, "central")})
    assert launch(adapter, "base", "feature-x", {})["ok"]
    entries = load(defaults)
    entries["base-feature-x"] = record_for(adapter.list_worksets()["base-feature-x"], "server")
    store(defaults, entries)

    result = launch(adapter, "base", "feature-x", {})

    assert result["default"] == {"action": "kept", "label": "server"}
    assert load(defaults)["base-feature-x"].label == "server"


def test_unpublished_launch_records_nothing(tmp_path, adapter, defaults):
    from powerspec.workset_launch import launch
    source = base(tmp_path, adapter, "central", "server")
    adapter.publish(Workset("base-feature-x", (Member("other", repo(tmp_path / "other")),)))
    store(defaults, {"base": record_for(source, "central")})

    result = launch(adapter, "base", "feature-x", {})

    assert not result["ok"]
    assert "base-feature-x" not in load(defaults)


def test_stale_source_default_records_nothing(tmp_path, adapter, defaults):
    from powerspec.workset_launch import launch
    base(tmp_path, adapter, "central", "server")
    outdated = Workset("base", (Member("central", tmp_path / "central"),))
    store(defaults, {"base": record_for(outdated, "central")})

    result = launch(adapter, "base", "feature-x", {})

    assert result["ok"] and result["default"] == {"action": "skipped", "reason": "members changed"}
    assert "base-feature-x" not in load(defaults)


def test_append_refreshes_a_current_default_snapshot(tmp_path, adapter, defaults):
    from powerspec.worksets import add_source
    source = base(tmp_path, adapter, "central")
    store(defaults, {"base": record_for(source, "central")})

    result = add_source(adapter, "base", repo(tmp_path / "web"))

    assert result["action"] == "appended" and result["default"] == "refreshed"
    entry = load(defaults)["base"]
    assert entry.label == "central"
    assert normalize(tmp_path / "web") in {normalize(item) for item in entry.members}


def test_append_leaves_a_stale_default_untouched(tmp_path, adapter, defaults):
    from powerspec.worksets import add_source
    base(tmp_path, adapter, "central")
    outdated = record_for(Workset("base", (Member("central", tmp_path / "central"), Member("x", tmp_path / "x"))), "central")
    store(defaults, {"base": outdated})

    result = add_source(adapter, "base", repo(tmp_path / "web"))

    assert result["default"] == "stale: members changed"
    assert load(defaults)["base"] == outdated


def test_failed_append_leaves_the_default_untouched(tmp_path, adapter, defaults, monkeypatch):
    from powerspec.worksets import add_source
    source = base(tmp_path, adapter, "central")
    entry = record_for(source, "central")
    store(defaults, {"base": entry})
    monkeypatch.setattr(adapter, "append_member", lambda *a: (_ for _ in ()).throw(ValueError("append failed")))

    with pytest.raises(ValueError, match="append failed"):
        add_source(adapter, "base", repo(tmp_path / "web"))
    assert load(defaults)["base"] == entry

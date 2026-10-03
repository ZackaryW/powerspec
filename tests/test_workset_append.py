import pytest

from powerspec.workset_openspec import OpenSpec, Workset, Member


def simulated_registry(tmp_path, monkeypatch, failure=None):
    adapter = OpenSpec(tmp_path)
    original = Workset("demo", (Member("first", tmp_path / "first"),), "code")
    additional = Member("second", tmp_path / "second")
    registry = {original.name: original}
    commands = []
    monkeypatch.setattr(adapter, "list_worksets", lambda: dict(registry))

    def call(*args):
        commands.append(args)
        if failure:
            failure(args, registry, original)
        if args[:2] == ("workset", "remove"):
            registry.pop(args[2])
        else:
            members = []
            for i, arg in enumerate(args):
                if arg == "--member":
                    name, path = args[i + 1].split("=", 1)
                    members.append(Member(name, type(tmp_path)(path)))
            tool = args[args.index("--tool") + 1] if "--tool" in args else None
            registry[args[2]] = Workset(args[2], tuple(members), tool)
        return {}

    monkeypatch.setattr(adapter, "call", call)
    return adapter, original, additional, registry, commands


def test_append_preserves_order_and_tool(tmp_path, monkeypatch):
    adapter, old, member, registry, commands = simulated_registry(tmp_path, monkeypatch)
    assert adapter.append_member(old, member) == "appended"
    assert registry["demo"] == Workset("demo", (*old.members, member), "code")
    assert commands[0] == ("workset", "remove", "demo", "--yes")
    assert all(c[:2] in (("workset", "remove"), ("workset", "create")) for c in commands)


def test_recreation_failure_restores_original(tmp_path, monkeypatch):
    def fail(args, registry, old):
        if args[:2] == ("workset", "create") and sum(a == "--member" for a in args) == 2:
            raise ValueError("injected create failure")
    adapter, old, member, registry, _ = simulated_registry(tmp_path, monkeypatch, fail)
    with pytest.raises(ValueError, match="original workset restored"):
        adapter.append_member(old, member)
    assert registry["demo"] == old


def test_concurrent_recreation_is_not_removed(tmp_path, monkeypatch):
    def fail(args, registry, old):
        if args[:2] == ("workset", "create"):
            registry["demo"] = Workset("demo", (Member("concurrent", tmp_path / "third"),), None)
            raise ValueError("name taken")
    adapter, old, member, registry, commands = simulated_registry(tmp_path, monkeypatch, fail)
    with pytest.raises(ValueError, match="different workset"):
        adapter.append_member(old, member)
    assert registry["demo"].members[0].name == "concurrent"
    assert sum(c[1] == "remove" for c in commands) == 1


def test_failure_to_restore_reports_original_definition(tmp_path, monkeypatch):
    def fail(args, registry, old):
        if args[:2] == ("workset", "create"):
            raise ValueError("service unavailable")
    adapter, old, member, registry, _ = simulated_registry(tmp_path, monkeypatch, fail)
    with pytest.raises(ValueError, match="Original definition:") as error:
        adapter.append_member(old, member)
    assert '"tool":"code"' in str(error.value)
    assert '"name":"first"' in str(error.value)
    assert "demo" not in registry


def test_changed_snapshot_fails_before_deletion(tmp_path, monkeypatch):
    adapter, old, member, registry, commands = simulated_registry(tmp_path, monkeypatch)
    registry["demo"] = Workset("demo", old.members, "cursor")
    with pytest.raises(ValueError, match="changed"):
        adapter.append_member(old, member)
    assert commands == []


def test_lost_creation_response_accepts_verified_result(tmp_path, monkeypatch):
    def fail(args, registry, old):
        if args[:2] == ("workset", "create"):
            registry["demo"] = Workset("demo", (*old.members, Member("second", tmp_path / "second")), old.tool)
            raise ValueError("response lost")
    adapter, old, member, registry, commands = simulated_registry(tmp_path, monkeypatch, fail)
    assert adapter.append_member(old, member) == "appended"
    assert len(registry["demo"].members) == 2
    assert len(commands) == 2


def test_failed_removal_preserves_original(tmp_path, monkeypatch):
    def fail(args, registry, old):
        if args[:2] == ("workset", "remove"):
            raise ValueError("remove failed")
    adapter, old, member, registry, commands = simulated_registry(tmp_path, monkeypatch, fail)
    with pytest.raises(ValueError, match="original workset preserved"):
        adapter.append_member(old, member)
    assert registry["demo"] == old
    assert len(commands) == 1


def test_duplicate_label_does_not_remove_definition(tmp_path, monkeypatch):
    from test_workset_helpers import repo
    from powerspec.worksets import add_source
    first_parent, second_parent = tmp_path / "a", tmp_path / "b"
    first_parent.mkdir()
    second_parent.mkdir()
    first, second = repo(first_parent / "same"), repo(second_parent / "same")
    adapter = OpenSpec(tmp_path)
    monkeypatch.setattr(adapter, "list_worksets", lambda: {"demo": Workset("demo", (Member("same", first),))})
    monkeypatch.setattr(adapter, "call", lambda *args: pytest.fail("conflict must be found before mutation"))
    with pytest.raises(ValueError, match="label conflict"):
        add_source(adapter, "demo", second)

from contextlib import contextmanager
from pathlib import Path

from powerspec.sources import SourceBinding
from powerspec.workspace import open_workspace


def put(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def setup(tmp_path):
    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    local = project / "openspec/.pspec"
    put(local / "config.toml", 'profile="@local/private"\n')
    put(local / "profiles/private.toml", 'contexts=["@local/private"]\n')
    put(local / "contexts/private.toml", '[[attach.context]]\nbody="Local"\n')
    builtin = tmp_path / "builtin"
    put(builtin / "profiles/global.toml", 'global=true\n')
    return project, builtin


def test_workspace_loads_consumer_local_resources_and_exclusions(tmp_path, monkeypatch):
    import powerspec.workspace as workspace

    project, builtin = setup(tmp_path)

    @contextmanager
    def resources():
        yield builtin

    monkeypatch.setattr(workspace, "builtin_catalog_root", resources)
    with open_workspace(project, agent="codex", source_mode="lookup") as loaded:
        assert loaded.consumer.git_root == project.resolve()
        assert [item.ref for item in loaded.bundle.profiles] == [
            "@builtin/global",
            "@local/private",
        ]
        assert [item.ref for item in loaded.bundle.contexts] == ["@local/private"]


def test_workspace_selects_lookup_or_acquisition_without_read_mode_acquisition(tmp_path, monkeypatch):
    import powerspec.workspace as workspace

    project, builtin = setup(tmp_path)
    put(project / "openspec/.pspec/config.toml", 'profile="@builtin/remote"\n')
    put(
        builtin / "profiles/remote.toml",
        'skills=["@gitsource/tools/skills/*"]\n'
        '[[source]]\nid="tools"\nprovider="git"\norigin="https://example.test/tools"\nreference="main"\n',
    )
    remote = tmp_path / "remote"
    put(remote / "skills/tool/SKILL.md", "---\nname: tool\ndescription: Tool.\n---\n")
    calls = []

    class Sources:
        def lookup(self, identity, recipe):
            calls.append("lookup")
            return SourceBinding(identity, recipe["origin"], recipe["reference"], "a" * 40, "s", "a", remote)

        def ensure(self, identity, recipe):
            calls.append("ensure")
            return self.lookup(identity, recipe)

    @contextmanager
    def resources():
        yield builtin

    monkeypatch.setattr(workspace, "builtin_catalog_root", resources)
    store = Sources()
    with open_workspace(project, agent="codex", source_mode="lookup", source_store=store):
        pass
    assert calls == ["lookup"]
    calls.clear()
    with open_workspace(project, agent="codex", source_mode="ensure", source_store=store):
        pass
    assert calls == ["ensure", "lookup"]


def test_workspace_only_manages_saucepan_binary_for_acquisition(tmp_path, monkeypatch):
    import powerspec.workspace as workspace

    project, builtin = setup(tmp_path)
    modes = []

    class Sources:
        def __init__(self, *, manage_binary):
            modes.append(manage_binary)

        def lookup(self, *_args, **_kwargs):
            raise AssertionError("local-only workspace performed remote lookup")

        def ensure(self, *_args, **_kwargs):
            raise AssertionError("local-only workspace performed remote acquisition")

    @contextmanager
    def resources():
        yield builtin

    monkeypatch.setattr(workspace, "builtin_catalog_root", resources)
    monkeypatch.setattr(workspace, "SaucepanSources", Sources)
    with open_workspace(project, agent="codex", source_mode="lookup"):
        pass
    with open_workspace(project, agent="codex", source_mode="ensure"):
        pass
    assert modes == [False, True]

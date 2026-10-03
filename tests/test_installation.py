from contextlib import contextmanager
from pathlib import Path

from powerspec.installation import install_consumer
from powerspec.sources import SourceBinding


def put(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def setup(tmp_path):
    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    put(project / "openspec/.pspec/config.toml", 'profile="@builtin/main"\n')
    builtin = tmp_path / "builtin"
    put(
        builtin / "profiles/main.toml",
        'scope="user"\nskills=["tools/skills/*"]\n'
        '[[source]]\nid="tools"\nprovider="git"\n'
        'origin="https://example.test/tools"\nreference="main"\n',
    )
    remote = tmp_path / "remote"
    put(remote / "skills/example/SKILL.md", "---\nname: example\ndescription: Example.\n---\n")
    return project, builtin, remote


def test_install_acquires_then_reuses_selected_skills_and_dispatcher(tmp_path, monkeypatch):
    import powerspec.workspace as workspace

    project, builtin, remote = setup(tmp_path)
    calls = []

    class Sources:
        def ensure(self, identity, recipe):
            calls.append((identity, dict(recipe)))
            return SourceBinding(identity, recipe["origin"], recipe["reference"], "a" * 40, "s", "a", remote)

    @contextmanager
    def resources():
        yield builtin

    monkeypatch.setattr(workspace, "builtin_catalog_root", resources)
    context = dict(home=tmp_path / "home", registry=tmp_path / "registry", source_store=Sources())
    first = install_consumer(project, agent="codex", **context)
    assert first.ok and first.provisioning.items[0].status == "installed"
    assert first.hooks.status == "installed"
    assert (tmp_path / "home/.codex/skills/example/SKILL.md").is_file()
    second = install_consumer(project, agent="codex", **context)
    assert second.ok and second.provisioning.items[0].status == "reused"
    assert second.hooks.status == "reused"
    assert len(calls) == 2


def test_install_reports_partial_skill_failure_without_removing_successes(tmp_path, monkeypatch):
    import powerspec.workspace as workspace

    project, builtin, remote = setup(tmp_path)
    put(remote / "skills/second/SKILL.md", "---\nname: second\ndescription: Second.\n---\n")
    foreign = tmp_path / "home/.codex/skills/example/SKILL.md"
    put(foreign, "---\nname: example\n---\nUser content\n")

    class Sources:
        def ensure(self, identity, recipe):
            return SourceBinding(identity, recipe["origin"], recipe["reference"], "a" * 40, "s", "a", remote)

    @contextmanager
    def resources():
        yield builtin

    monkeypatch.setattr(workspace, "builtin_catalog_root", resources)
    result = install_consumer(
        project,
        agent="codex",
        home=tmp_path / "home",
        registry=tmp_path / "registry",
        source_store=Sources(),
    )
    assert not result.ok
    assert {item.status for item in result.provisioning.items} == {"failed", "installed"}
    assert foreign.read_text(encoding="utf-8").endswith("User content\n")
    assert (tmp_path / "home/.codex/skills/second/SKILL.md").is_file()

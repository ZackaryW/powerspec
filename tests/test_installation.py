from contextlib import contextmanager
from pathlib import Path
import json

from powerspec.installation import install_consumer
from powerspec.sources import SourceBinding
from test_hook_reconciliation import hooks, provision, write_hooks, snapshot
from copy import deepcopy


def test_installation_explicit_hook_repair_preserves_native_content(tmp_path, monkeypatch, hooks):
    import powerspec.provisioning as provisioning
    import powerspec.workspace as workspace
    from powerspec.hooks import native_document
    project, builtin, remote = setup(tmp_path)
    current = native_document(hooks.agent)
    legacy = deepcopy(current)
    legacy['hooks']['SessionStart'][0]['matcher'] = 'startup|resume|clear'
    with monkeypatch.context() as patch:
        patch.setattr(provisioning, 'native_document', lambda _: legacy)
        assert provision(hooks).ok
    write_hooks(hooks, current)
    before = snapshot(hooks)
    class Sources:
        def ensure(self, identity, recipe):
            return SourceBinding(identity, recipe['origin'], 'main', 'a' * 40, 's', 'a', remote)
    @contextmanager
    def resources():
        yield builtin
    monkeypatch.setattr(workspace, 'builtin_catalog_root', resources)
    options = dict(agent=hooks.agent, home=hooks.home, registry=hooks.registry, source_store=Sources())
    assert not install_consumer(project, **options).ok
    repaired = install_consumer(project, repair_hooks=True, **options)
    assert repaired.ok and repaired.hooks.operation_id
    assert snapshot(hooks) == before


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
    hooks_path = context["home"] / ".codex/hooks.json"
    put(hooks_path, '{"unrelated":{"keep":true}}\n')
    first = install_consumer(project, agent="codex", **context)
    assert first.ok and first.provisioning.items[0].status == "installed"
    assert first.hooks.status == "installed"
    assert (tmp_path / "home/.codex/skills/example/SKILL.md").is_file()
    first_hooks = hooks_path.read_bytes()
    second = install_consumer(project, agent="codex", **context)
    assert second.ok and second.provisioning.items[0].status == "reused"
    assert second.hooks.status == "reused"
    assert len(calls) == 2
    assert hooks_path.read_bytes() == first_hooks
    hooks = json.loads(first_hooks)
    assert hooks["unrelated"] == {"keep": True}
    assert len(hooks["hooks"]["SessionStart"]) == 2


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

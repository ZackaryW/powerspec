from dataclasses import replace
from pathlib import Path

import pytest
from zuat.pub import AssetInspection, OperationResult, OperationStatus

from powerspec.catalog import Catalog, ConfigurationError
from powerspec.profiles import compose


def bundle(tmp_path, *, agent="codex"):
    root = tmp_path / "catalog"
    for name, scope in (("shared", "user"), ("local", "project")):
        folder = root / "skills" / name
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Test\n---\nBody")
        (folder / "inactive.md").write_text("Complete branch content")
        profile = root / "profiles" / f"{name}.toml"
        profile.parent.mkdir(exist_ok=True)
        profile.write_text(f'scope="{scope}"\nskills=["@builtin/{name}"]\n' +
                           ('profiles=["@builtin/shared"]\n' if name == "local" else ''))
    project = tmp_path / "project"
    project.mkdir()
    return compose(Catalog(builtin=root), "@builtin/local", agent=agent, project_root=project)


def test_scoped_provisioning_reuses_and_preserves_complete_resources(tmp_path):
    from powerspec.provisioning import plan_skills, provision_skills
    selected = bundle(tmp_path)
    plan = plan_skills(selected)
    assert {(p.ref, p.scope) for p in plan} == {("@builtin/shared", "user"), ("@builtin/local", "project")}
    assert all(p.profile and p.source.is_dir() and p.agent == "codex" for p in plan)
    context = dict(home=tmp_path / "home", registry=tmp_path / "registry")
    first = provision_skills(plan, **context)
    assert first.ok, first
    assert {item.status for item in first.items} == {"installed"}
    from powerspec.installed import installed_skill
    for name in ("shared", "local"):
        located = installed_skill("codex", name, cwd=tmp_path / "project", home=context["home"])
        assert (located.root / "inactive.md").read_text() == "Complete branch content"
    second = provision_skills(plan, **context)
    assert second.ok and {item.status for item in second.items} == {"reused"}
    # Excluding a profile changes contributions without removing installed skills.
    assert provision_skills((), **context).ok
    assert installed_skill("codex", "shared", cwd=tmp_path / "project", home=context["home"])


def test_foreign_and_modified_skills_are_preserved(tmp_path):
    from powerspec.provisioning import plan_skills, provision_skills
    plan = plan_skills(bundle(tmp_path))
    context = dict(home=tmp_path / "home", registry=tmp_path / "registry")
    foreign = context["home"] / ".codex/skills/shared/SKILL.md"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("---\nname: shared\n---\nUser content")
    result = provision_skills(plan, **context)
    assert not result.ok
    assert any(i.ref == "@builtin/shared" and i.status == "failed" for i in result.items)
    assert any(i.ref == "@builtin/local" and i.status == "installed" for i in result.items)
    assert foreign.read_text().endswith("User content")
    from powerspec.installed import installed_skill
    local = installed_skill("codex", "local", cwd=tmp_path / "project", home=context["home"])
    local.entrypoint.write_text("---\nname: local\n---\nLocal edits")
    again = provision_skills(plan, **context)
    assert not again.ok and all(i.status == "failed" for i in again.items)
    assert local.entrypoint.read_text().endswith("Local edits")


def test_invalid_targets_fail_before_adapter_calls(tmp_path):
    from powerspec.provisioning import plan_skills
    selected = bundle(tmp_path)
    target = selected.skills[0]
    for invalid in (replace(target, agent="unknown"), replace(target, scope="workspace"),
                    replace(target, scope="project", project_root=None)):
        with pytest.raises(ConfigurationError):
            plan_skills(replace(selected, skills=(invalid,)))


def test_identical_foreign_copy_is_not_adopted_when_inspection_is_incomplete(tmp_path, monkeypatch):
    import shutil
    import powerspec.provisioning as p
    plan = p.plan_skills(bundle(tmp_path))[:1]
    home = tmp_path / "home"
    destination = home / ".codex/skills/shared"
    shutil.copytree(plan[0].source, destination)
    monkeypatch.setattr(p, "inspect_asset", lambda a, **kw: AssetInspection(
        "indeterminate", a.agent, a.kind, a.name, a.scope, completeness="partial"))
    monkeypatch.setattr(p, "install", lambda *a, **kw: pytest.fail("must not adopt foreign bytes"))
    assert not p.provision_skills(plan, home=home, registry=tmp_path / "registry").ok


def test_unsupported_scope_does_not_switch_or_install(tmp_path, monkeypatch):
    import powerspec.provisioning as p
    plan = p.plan_skills(bundle(tmp_path))
    monkeypatch.setattr(p, "inspect_asset", lambda a, **kw: AssetInspection(
        "unsupported", a.agent, a.kind, a.name, a.scope, diagnostics=("scope unsupported",)))
    monkeypatch.setattr(p, "install", lambda *a, **kw: pytest.fail("must not install"))
    result = p.provision_skills(plan, home=tmp_path / "home", registry=tmp_path / "registry")
    assert not result.ok and len(result.items) == 2
    assert all(i.diagnostics == ("scope unsupported",) for i in result.items)


def test_requests_never_use_all_agent_default_or_force(tmp_path, monkeypatch):
    import powerspec.provisioning as p
    plan = p.plan_skills(bundle(tmp_path))
    calls = []
    monkeypatch.setattr(p, "inspect_asset", lambda a, **kw: AssetInspection("absent", a.agent, a.kind, a.name, a.scope))
    def install(request, **context):
        calls.append((request, context))
        return OperationResult("install", OperationStatus.PARTIAL, diagnostics=("write interrupted",))
    monkeypatch.setattr(p, "install", install)
    result = p.provision_skills(plan, home=tmp_path / "home", registry=tmp_path / "registry")
    assert not result.ok and len(result.items) == len(calls) == 2
    assert all(r.agents == ("codex",) and not r.force for r, _ in calls)
    assert {c["project_root"] for _, c in calls} == {None, (tmp_path / "project").resolve()}


def test_reviewed_bundle_installs_upstream_and_manifest_resources(tmp_path, monkeypatch):
    from powerspec.provisioning import plan_skills, provision_skills
    from powerspec.installed import installed_skill
    from powerspec.resources import builtin_catalog_root
    from powerspec.skills import resolve_skill
    project = tmp_path / "project"
    project.mkdir()
    with builtin_catalog_root() as root:
        selected = compose(Catalog(builtin=root), "@builtin/python-simple-cli", agent="codex",
                           exclude_profiles=["@builtin/zmem-lifecycle", "@builtin/adhd-friendly"])
        plan = plan_skills(selected)
        assert "pspec-bdd" not in {p.name for p in plan}
        result = provision_skills(plan, home=tmp_path / "home", registry=tmp_path / "registry")
    assert result.ok, result
    ordinary = installed_skill("codex", "openspec-apply-change", cwd=project, home=tmp_path / "home")
    assert not (ordinary.root / "pspec.toml").exists()
    from typer.testing import CliRunner
    from powerspec.cli import app
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "home/.codex"))
    monkeypatch.chdir(project)
    fallback = CliRunner().invoke(app, ["skill", "openspec-apply-change", "--agent", "codex"])
    assert fallback.exit_code == 0 and fallback.stdout.strip() == "null", fallback.output
    tdd = installed_skill("codex", "pspec-tdd", cwd=project, home=tmp_path / "home")
    assert (tdd.root / "languages/python.md").is_file()
    resolved = resolve_skill(tdd.root, selected, None)
    assert resolved.status == "resolved"
    assert not (project / ".agents").exists()

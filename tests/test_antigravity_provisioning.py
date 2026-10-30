"""Antigravity skills and the keyed hook dispatcher, provisioned through ZuAT."""
from contextlib import contextmanager
import json

from typer.testing import CliRunner

from powerspec.cli import app
from powerspec.hooks import native_document
from powerspec.installation import install_consumer
from powerspec.provisioning import plan_skills, provision_hooks, provision_skills
from powerspec.sources import SourceBinding
from test_installation import put, setup
from test_provisioning import bundle

OTHER = {"PostToolUse": [{"matcher": "run_command", "hooks": [{"command": "./lint.sh"}]}]}


def hooks_file(home):
    return home / ".gemini/config/hooks.json"


def test_dispatcher_installs_as_a_keyed_entry_beside_other_hooks_and_reuses(tmp_path):
    home, registry = tmp_path / "home", tmp_path / "registry"
    put(hooks_file(home), json.dumps({"lint": OTHER}))

    first = provision_hooks("antigravity", home=home, registry=registry)
    second = provision_hooks("antigravity", home=home, registry=registry)

    assert (first.status, second.status) == ("installed", "reused")
    assert json.loads(hooks_file(home).read_text(encoding="utf-8")) == {"lint": OTHER, **native_document("antigravity")}


def test_foreign_powerspec_entry_is_reported_and_preserved(tmp_path):
    home, registry = tmp_path / "home", tmp_path / "registry"
    put(hooks_file(home), json.dumps({"powerspec": OTHER}))
    before = hooks_file(home).read_bytes()

    outcome = provision_hooks("antigravity", home=home, registry=registry)

    assert outcome.status == "failed" and outcome.diagnostics
    assert hooks_file(home).read_bytes() == before


def test_stale_receipt_needs_explicit_repair_which_keeps_native_bytes(tmp_path, monkeypatch):
    import powerspec.provisioning as provisioning

    home, registry = tmp_path / "home", tmp_path / "registry"
    current = native_document("antigravity")
    legacy = json.loads(json.dumps(current))
    legacy["powerspec"]["SessionStart"][0]["timeout"] = 4
    with monkeypatch.context() as patch:
        patch.setattr(provisioning, "native_document", lambda _agent: legacy)
        assert provision_hooks("antigravity", home=home, registry=registry).ok
    put(hooks_file(home), json.dumps(current, indent=3))
    before = hooks_file(home).read_bytes()

    refused = provision_hooks("antigravity", home=home, registry=registry)
    repaired = provision_hooks("antigravity", home=home, registry=registry, repair_hooks=True)

    assert refused.status == "failed" and "--repair-hooks" in " ".join(refused.diagnostics)
    assert repaired.status == "updated" and repaired.operation_id
    assert hooks_file(home).read_bytes() == before
    assert provision_hooks("antigravity", home=home, registry=registry).status == "reused"


def test_skills_install_to_antigravity_user_and_project_locations(tmp_path):
    plans = plan_skills(bundle(tmp_path, agent="antigravity"))
    context = dict(home=tmp_path / "home", registry=tmp_path / "registry")

    first = provision_skills(plans, **context)
    second = provision_skills(plans, **context)

    assert first.ok and {item.status for item in first.items} == {"installed"}
    assert second.ok and {item.status for item in second.items} == {"reused"}
    assert (tmp_path / "home/.gemini/config/skills/shared/SKILL.md").is_file()
    assert (tmp_path / "project/.agents/skills/local/SKILL.md").is_file()


def test_init_installs_skills_and_dispatcher_for_antigravity(tmp_path, monkeypatch):
    import powerspec.workspace as workspace

    project, builtin, remote = setup(tmp_path)

    class Sources:
        def ensure(self, identity, recipe):
            return SourceBinding(identity, recipe["origin"], recipe["reference"], "a" * 40, "s", "a", remote)

    @contextmanager
    def resources():
        yield builtin

    monkeypatch.setattr(workspace, "builtin_catalog_root", resources)
    context = dict(home=tmp_path / "home", registry=tmp_path / "registry", source_store=Sources())

    first = install_consumer(project, agent="antigravity", **context)
    second = install_consumer(project, agent="antigravity", **context)

    assert first.ok and (first.provisioning.items[0].status, first.hooks.status) == ("installed", "installed")
    assert second.ok and (second.provisioning.items[0].status, second.hooks.status) == ("reused", "reused")
    assert (tmp_path / "home/.gemini/config/skills/example/SKILL.md").is_file()
    assert json.loads(hooks_file(tmp_path / "home").read_text(encoding="utf-8")) == native_document("antigravity")


def test_doctor_rejects_antigravity_before_any_probe(tmp_path, monkeypatch):
    import powerspec.cli.doctor as doctor

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(doctor, "doctor_consumer", lambda *a, **k: (_ for _ in ()).throw(AssertionError("probed")))

    result = CliRunner().invoke(app, ["doctor", "--agent", "antigravity"])

    assert result.exit_code != 0
    assert "codex and claude" in result.output

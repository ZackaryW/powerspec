import json
from pathlib import Path

from powerspec.doctoring import doctor_consumer
from powerspec.utils.inspection import ExecutableResult


def setup(tmp_path):
    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    state = project / "openspec/.pspec"
    state.mkdir(parents=True)
    (state / "config.toml").write_text("[vars]\n", encoding="utf-8")
    return project


def test_doctor_reports_named_checks_without_repair(tmp_path, monkeypatch):
    import powerspec.doctoring as doctoring

    project = setup(tmp_path)
    observed = []

    def inspect(argv, **kwargs):
        observed.append(tuple(argv))
        if argv[0] == "git":
            return ExecutableResult("ok", "git", 0, "git version 2.50", "", "2.50")
        if argv[0] == "openspec":
            return ExecutableResult("ok", "openspec", 0, "1.13.2", "", "1.13.2")
        return ExecutableResult("missing")

    monkeypatch.setattr(doctoring, "inspect_executable", inspect)
    result = doctor_consumer(project, saucepan_path=tmp_path / "saucepan")
    assert not result.ok
    assert [item.name for item in result.checks] == ["consumer", "git", "openspec", "saucepan"]
    assert result.checks[-1].status == "failed"
    assert not (tmp_path / "saucepan").exists()
    assert observed[-1][0] == str(tmp_path / "saucepan")


def test_doctor_cli_json_exits_nonzero_for_missing_consumer(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from powerspec.cli import app

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["doctor", "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert any(item["name"] == "consumer" and item["status"] == "failed" for item in payload["checks"])


def test_doctor_rejects_old_openspec_version(tmp_path, monkeypatch):
    import powerspec.doctoring as doctoring

    project = setup(tmp_path)

    def inspect(argv, **kwargs):
        version = "1.12.9" if argv[0] == "openspec" else "0.6.0"
        return ExecutableResult("ok", argv[0], 0, version, "", version)

    monkeypatch.setattr(doctoring, "inspect_executable", inspect)
    result = doctor_consumer(project, saucepan_path=tmp_path / "saucepan")
    check = next(item for item in result.checks if item.name == "openspec")
    assert check.status == "failed" and "older than 1.13.2" in check.detail

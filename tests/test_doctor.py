import json
from pathlib import Path
import pytest

from powerspec.doctoring import doctor_consumer
from powerspec.utils.inspection import ExecutableResult


def setup(tmp_path):
    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    state = project / "openspec/.pspec"
    state.mkdir(parents=True)
    (state / "config.toml").write_text("[vars]\n", encoding="utf-8")
    return project


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.delenv('POWERSPEC_MILKPAN', raising=False)
    monkeypatch.setenv('MILKPAN_HOME', str(tmp_path / 'milkpan'))
    monkeypatch.setattr('urllib.request.urlopen', lambda *a, **k: pytest.fail('doctor network'))


def tools(milkpan_version):
    def inspect(argv, **kwargs):
        if argv[0] == "git":
            return ExecutableResult("ok", "git", 0, "git version 2.50", "", "2.50")
        if argv[0] == "openspec":
            return ExecutableResult("ok", "openspec", 0, "1.14.3", "", "1.14.3")
        if milkpan_version is None:
            return ExecutableResult("missing")
        return ExecutableResult("ok", argv[0], 0, f"milkpan {milkpan_version}", "", milkpan_version)
    return inspect


def test_doctor_reports_named_checks_without_repair(tmp_path, monkeypatch):
    import powerspec.doctoring as doctoring

    project = setup(tmp_path)
    monkeypatch.setattr(doctoring, "inspect_executable", tools(None))
    result = doctor_consumer(project, milkpan_home=tmp_path / "milkpan")
    assert not result.ok
    assert [item.name for item in result.checks] == ["consumer", "git", "openspec", "milkpan", "milkpan-installation", "milkpan-sources", "guidance"]
    assert result.checks[3].status == "failed"
    assert "init or upgrade prepares it" in result.checks[4].detail
    assert not (tmp_path / "milkpan").exists(), "doctor never provisions"


def test_doctor_cli_json_exits_nonzero_for_missing_consumer(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from powerspec.cli import app

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["doctor", "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert any(item["name"] == "consumer" and item["status"] == "failed" for item in payload["checks"])


@pytest.mark.parametrize("openspec_version", ["1.12.9", "1.13.2", "1.14.2"])
def test_doctor_rejects_old_openspec_version(tmp_path, monkeypatch, openspec_version):
    import powerspec.doctoring as doctoring

    project = setup(tmp_path)

    def inspect(argv, **kwargs):
        version = openspec_version if argv[0] == "openspec" else "0.3.0"
        return ExecutableResult("ok", argv[0], 0, version, "", version)

    monkeypatch.setattr(doctoring, "inspect_executable", inspect)
    result = doctor_consumer(project, milkpan_path=tmp_path / "standalone")
    check = next(item for item in result.checks if item.name == "openspec")
    assert check.status == "failed" and "older than 1.14.3" in check.detail


@pytest.mark.parametrize("version,status", [("0.3.0", "ok"), ("0.3.7", "ok"), ("0.2.0", "failed"), ("1.0.0", "failed")])
def test_milkpan_compatibility_is_its_release_line(tmp_path, monkeypatch, version, status):
    import powerspec.doctoring as doctoring

    monkeypatch.setattr(doctoring, "inspect_executable", tools(version))
    result = doctor_consumer(setup(tmp_path), milkpan_path=tmp_path / "standalone")
    assert next(item for item in result.checks if item.name == "milkpan").status == status


@pytest.mark.parametrize('json_output', [False, True])
def test_doctor_labels_standalone_without_implying_source_readiness(tmp_path, monkeypatch, json_output):
    from typer.testing import CliRunner
    from powerspec.cli import app
    monkeypatch.setattr('powerspec.doctoring.inspect_executable', tools('0.3.0'))
    monkeypatch.setenv('POWERSPEC_MILKPAN', str(tmp_path / 'standalone'))
    monkeypatch.chdir(setup(tmp_path))
    result = CliRunner().invoke(app, ['doctor', *(['--json'] if json_output else [])])
    assert result.exit_code == 0, result.output
    if json_output:
        check = next(item for item in json.loads(result.stdout)['checks'] if item['name'] == 'milkpan')
        assert check['status'] == 'ok'
        detail = check['detail']
    else:
        detail = result.stdout
    assert 'executable compatible' in detail
    assert 'selected-source readiness not checked' in result.stdout
    assert 'standalone' in result.stdout
    assert not (tmp_path / 'standalone').exists()


@pytest.mark.parametrize('state,status,code', [('supported', 'ok', 0), ('unsupported', 'warning', 0), ('absent', 'failed', 1)])
def test_managed_link_state_is_reported_separately(tmp_path, monkeypatch, state, status, code):
    from typer.testing import CliRunner
    from powerspec.cli import app
    monkeypatch.setattr('powerspec.doctoring.inspect_executable', tools('0.3.0'))
    monkeypatch.setattr('powerspec.doctoring.managed_state', lambda home: state)
    monkeypatch.chdir(setup(tmp_path))
    result = CliRunner().invoke(app, ['doctor', '--json'])
    assert result.exit_code == code, result.output
    checks = {item['name']: item for item in json.loads(result.stdout)['checks']}
    assert checks['milkpan-installation']['status'] == status
    assert checks['milkpan-sources']['status'] == 'warning'
    if state == 'unsupported':
        assert 'next init or upgrade switches it' in checks['milkpan-installation']['detail']

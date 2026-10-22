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


def test_doctor_reports_named_checks_without_repair(tmp_path, monkeypatch):
    import powerspec.doctoring as doctoring

    project = setup(tmp_path)
    observed = []

    def inspect(argv, **kwargs):
        observed.append(tuple(argv))
        if argv[0] == "git":
            return ExecutableResult("ok", "git", 0, "git version 2.50", "", "2.50")
        if argv[0] == "openspec":
            return ExecutableResult("ok", "openspec", 0, "1.14.3", "", "1.14.3")
        return ExecutableResult("missing")

    monkeypatch.setattr(doctoring, "inspect_executable", inspect)
    result = doctor_consumer(project, saucepan_path=tmp_path / "saucepan")
    assert not result.ok
    assert [item.name for item in result.checks] == ["consumer", "git", "openspec", "saucepan", "saucepan-installation", "saucepan-sources", "guidance"]
    assert result.checks[3].status == "failed"
    assert result.checks[-1].status == "warning"
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


@pytest.mark.parametrize("openspec_version", ["1.12.9", "1.13.2", "1.14.2"])
def test_doctor_rejects_old_openspec_version(tmp_path, monkeypatch, openspec_version):
    import powerspec.doctoring as doctoring

    project = setup(tmp_path)

    def inspect(argv, **kwargs):
        version = openspec_version if argv[0] == "openspec" else "0.10.0"
        return ExecutableResult("ok", argv[0], 0, version, "", version)

    monkeypatch.setattr(doctoring, "inspect_executable", inspect)
    result = doctor_consumer(project, saucepan_path=tmp_path / "saucepan")
    check = next(item for item in result.checks if item.name == "openspec")
    assert check.status == "failed" and "older than 1.14.3" in check.detail

    from typer.testing import CliRunner
    from powerspec.cli import app
    config = project / "openspec/.pspec/config.toml"
    before = config.read_bytes()
    monkeypatch.chdir(project)
    monkeypatch.setenv("POWERSPEC_SAUCEPAN", str(tmp_path / "standalone"))
    cli_result = CliRunner().invoke(app, ["doctor", "--json"])
    assert cli_result.exit_code == 1
    checks = json.loads(cli_result.stdout)["checks"]
    assert next(item for item in checks if item["name"] == "openspec")["status"] == "failed"
    assert config.read_bytes() == before
    assert not (tmp_path / "standalone").exists()


@pytest.mark.parametrize('json_output', [False, True])
def test_doctor_labels_binary_check_without_implying_source_readiness(tmp_path, monkeypatch, json_output):
    from typer.testing import CliRunner
    from powerspec.cli import app
    def inspect(argv, **kwargs):
        version = '1.14.3' if argv[0] == 'openspec' else '0.10.0'
        return ExecutableResult('ok', argv[0], 0, version, '', version)
    monkeypatch.setattr('powerspec.doctoring.inspect_executable', inspect)
    monkeypatch.setenv('POWERSPEC_SAUCEPAN', str(tmp_path / 'standalone'))
    monkeypatch.chdir(setup(tmp_path))
    result = CliRunner().invoke(app, ['doctor', *(['--json'] if json_output else [])])
    assert result.exit_code == 0, result.output
    if json_output:
        check = next(item for item in json.loads(result.stdout)['checks'] if item['name'] == 'saucepan')
        assert check['status'] == 'ok'
        detail = check['detail']
    else:
        detail = result.stdout
    assert 'executable compatible' in detail
    assert 'selected-source readiness not checked' in result.stdout
    assert 'standalone' in result.stdout

@pytest.mark.parametrize('state', ['ready', 'pending', 'conflict', 'absent', 'unmanaged'])
@pytest.mark.parametrize('json_output', [False, True])
def test_cli_reports_managed_state_separately(tmp_path, monkeypatch, state, json_output):
    from typer.testing import CliRunner
    from powerspec.cli import app
    from powerspec.saucepan_provider import SetupStatus
    from test_managed_setup_contract import observation
    from powerspec.saucepan_tool import saucepan_executable_path
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: tmp_path))
    monkeypatch.delenv('POWERSPEC_SAUCEPAN', raising=False)
    target = saucepan_executable_path()
    target.parent.mkdir(parents=True)
    target.write_bytes(b'fixture')
    def inspect(argv, **kwargs):
        version = '1.14.3' if argv[0] == 'openspec' else '0.11.0'
        return ExecutableResult('ok', argv[0], 0, version, '', version)
    monkeypatch.setattr('powerspec.doctoring.inspect_executable', inspect)
    # Install this seam in the owning module; doctor must call the same contract.
    monkeypatch.setattr('powerspec.saucepan_tool.inspect_managed_status', lambda *a, **k: SetupStatus.model_validate(observation(target, state)))
    monkeypatch.chdir(setup(tmp_path))
    result = CliRunner().invoke(app, ['doctor', *(['--json'] if json_output else [])])
    assert result.exit_code == (0 if state == 'ready' else 1), result.output
    if json_output:
        checks = {item['name']: item for item in json.loads(result.stdout)['checks']}
        assert checks['saucepan']['status'] == 'ok'
        assert state in checks['saucepan-installation']['detail']
        assert checks['saucepan-sources']['status'] == 'warning'
    else:
        assert state in result.stdout and 'selected-source readiness not checked' in result.stdout

@pytest.mark.parametrize('exists', [False, True])
@pytest.mark.parametrize('json_output', [False, True])
def test_cli_absent_and_legacy_default_are_observations_only(tmp_path, monkeypatch, exists, json_output):
    from typer.testing import CliRunner
    from powerspec.cli import app
    from powerspec.saucepan_tool import saucepan_executable_path
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: tmp_path))
    monkeypatch.delenv('POWERSPEC_SAUCEPAN', raising=False)
    target = saucepan_executable_path()
    if exists:
        target.parent.mkdir(parents=True)
        target.write_bytes(b'legacy')
    def inspect(argv, **kwargs):
        if argv[0] == str(target) and not exists:
            return ExecutableResult('missing')
        version = '1.14.3' if argv[0] == 'openspec' else '0.10.0'
        return ExecutableResult('ok', argv[0], 0, version, '', version)
    monkeypatch.setattr('powerspec.doctoring.inspect_executable', inspect)
    monkeypatch.setattr('urllib.request.urlopen', lambda *a, **k: pytest.fail('doctor network'))
    monkeypatch.chdir(setup(tmp_path))
    result = CliRunner().invoke(app, ['doctor', *(['--json'] if json_output else [])])
    assert result.exit_code == 1
    assert ('migration' if exists else 'absent') in result.stdout
    assert target.parent.parent.exists() == exists
    if exists:
        assert target.read_bytes() == b'legacy'

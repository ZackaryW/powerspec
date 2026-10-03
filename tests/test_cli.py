"""Behavior at the public CLI boundary, including installed console scripts."""

import os
from pathlib import Path
import subprocess
import sys
import sysconfig

import pytest
from typer.testing import CliRunner


COMMANDS = ("init", "status", "sync", "upgrade", "doctor", "config", "state", "resolve")


def invoke(args):
    # Import lazily so the existing entrypoint can establish the first red test.
    from powerspec.cli import app

    return CliRunner().invoke(app, args)


def console(name):
    suffix = ".exe" if os.name == "nt" else ""
    return str(Path(sysconfig.get_path("scripts")) / (name + suffix))


def run_process(args, cwd, *, home=None):
    environment = {**os.environ, "NO_COLOR": "1", "TERM": "dumb"}
    if home is not None:
        environment.update(HOME=str(home), USERPROFILE=str(home))
    return subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, timeout=15,
        env=environment,
    )


def test_existing_entrypoint_becomes_command_help(tmp_path):
    result = run_process([sys.executable, "-c", "import powerspec; powerspec.main()"], tmp_path)
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert all(command in result.stdout for command in COMMANDS)
    assert result.stderr == ""


@pytest.mark.parametrize("name", ["pspec", "powerspec"])
@pytest.mark.parametrize("args", [[], ["--help"]])
def test_installed_aliases_show_help(name, args, tmp_path):
    result = run_process([console(name), *args], tmp_path)
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert all(command in result.stdout for command in COMMANDS)
    assert result.stderr == ""
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("command", COMMANDS)
def test_command_help_does_not_require_arguments(command):
    result = invoke([command, "--help"])
    assert result.exit_code == 0
    assert "placeholder" not in result.stdout.lower()
    assert result.stderr == ""


def test_init_does_not_create_a_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = invoke(["init"])
    assert result.exit_code == 1
    assert list(tmp_path.iterdir()) == []


def test_sync_without_consumer_reports_configuration_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = invoke(["sync"])
    assert result.exit_code == 1 and result.stdout == ""
    assert "no owning" in result.stderr.lower()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("args", [
    ["unknown"], ["--unknown"], ["skill"],
    ["skill", "pspec-tdd"], ["skill", "--agent", "codex"],
    ["skill", "pspec-tdd", "--agent"], ["hook"], ["hook", "sessionStart"],
    ["flush", "--change"],
    ["resolve", "skill"], ["resolve", "hook"], ["state", "clear", "--change"],
    ["sync", "--unknown"],
    ["install"], ["install", "--unknown"],
    ["upgrade"], ["upgrade", "--unknown"],
])
def test_invalid_syntax_is_a_usage_error(args):
    result = invoke(args)
    assert result.exit_code == 2
    assert "error" in result.stderr.lower()
    assert "not implemented" not in result.stderr.lower()
    assert result.stdout == ""


@pytest.mark.parametrize("name", ["pspec", "powerspec"])
def test_installed_aliases_report_upgrade_without_consumer(name, tmp_path):
    result = run_process(
        [console(name), "upgrade", "--agent", "codex"], tmp_path,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "no owning" in result.stderr.lower()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("name", ["pspec", "powerspec"])
def test_installed_entrypoints_clear_one_change(name, tmp_path):
    project = tmp_path / "project"
    state = project / "openspec/.pspec"
    state.mkdir(parents=True)
    subprocess.run(["git", "init", "--quiet", str(project)], check=True)
    (state / "config.toml").write_text("[vars]\npersistent = true\n")
    (state / "current.toml").write_text(
        '[vars]\nshared = "keep"\n[_change.example]\nanswer = "clear"\n'
    )
    result = run_process([console(name), "state", "clear", "--change", "example"], project)
    assert result.returncode == 0 and result.stderr == ""
    assert result.stdout.startswith("updated:")
    rendered = (state / "current.toml").read_text()
    assert 'shared = "keep"' in rendered and "_change" not in rendered
    assert 'persistent = true' in (state / "config.toml").read_text()


@pytest.mark.parametrize("name", ["pspec", "powerspec"])
def test_installed_entrypoints_report_missing_skill(name, tmp_path):
    result = run_process(
        [console(name), "resolve", "skill", "pspec-tdd", "--agent", "codex", "--json"], tmp_path,
        home=tmp_path / "empty-home",
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "missing" in result.stderr.lower() and "pspec-tdd" in result.stderr
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("module", ["powerspec", "powerspec.cli"])
def test_import_is_silent(module, tmp_path):
    result = run_process([sys.executable, "-c", f"import {module}"], tmp_path)
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""
    assert list(tmp_path.iterdir()) == []

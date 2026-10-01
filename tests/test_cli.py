"""Behavior at the public CLI boundary, including installed console scripts."""

import os
from pathlib import Path
import subprocess
import sys
import sysconfig

import pytest
from typer.testing import CliRunner


COMMANDS = ("init", "skill", "hook", "sync", "flush", "upgrade")
PLACEHOLDER_COMMANDS = ("init", "hook", "sync", "flush", "upgrade")
VALID_INVOCATIONS = [
    ["init"],
    ["init", "--agent", "codex"],
    ["hook", "sessionStart"],
    ["sync"],
    ["upgrade"],
    ["flush"],
    ["flush", "--change", "example"],
]


def invoke(args):
    # Import lazily so the existing entrypoint can establish the first red test.
    from powerspec.cli import app

    return CliRunner().invoke(app, args)


def console(name):
    suffix = ".exe" if os.name == "nt" else ""
    return str(Path(sysconfig.get_path("scripts")) / (name + suffix))


def run_process(args, cwd):
    return subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, timeout=15,
        env={**os.environ, "NO_COLOR": "1", "TERM": "dumb"},
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
    if command in PLACEHOLDER_COMMANDS:
        assert "placeholder" in result.stdout.lower()
    else:
        assert "placeholder" not in result.stdout.lower()
    assert result.stderr == ""
    if command == "skill":
        assert all(option in result.stdout for option in ("NAME", "--agent", "--change", "--selected", "--json"))


def snapshot(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes() if path.is_file() else None
        for path in root.rglob("*")
    }


@pytest.mark.parametrize("args", VALID_INVOCATIONS)
def test_placeholders_fail_without_output_or_state_changes(args, tmp_path, monkeypatch):
    project = tmp_path / "project"
    state = project / "openspec" / ".pspec"
    state.mkdir(parents=True)
    (state / "config.toml").write_text('[vars]\nlanguage = "python"\n')
    (state / "current.toml").write_text('[_change.example]\nlanguage = "rust"\n')
    agent_home = tmp_path / "home"
    agent_home.mkdir()
    (agent_home / "settings.json").write_text('{"existing": true}\n')
    monkeypatch.setenv("HOME", str(agent_home))
    monkeypatch.setenv("USERPROFILE", str(agent_home))
    monkeypatch.setenv("CODEX_HOME", str(agent_home / ".codex"))
    monkeypatch.chdir(project)
    before = snapshot(tmp_path)

    result = invoke(args)

    assert result.exit_code == 1
    assert result.stdout == ""
    assert args[0] in result.stderr
    assert "not implemented" in result.stderr.lower()
    assert snapshot(tmp_path) == before


def test_init_does_not_create_a_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = invoke(["init"])
    assert result.exit_code == 1
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("args", [
    ["unknown"], ["--unknown"], ["skill"],
    ["skill", "pspec-tdd"], ["skill", "--agent", "codex"],
    ["skill", "pspec-tdd", "--agent"], ["hook"], ["sync", "--unknown"],
    ["upgrade", "--unknown"],
])
def test_invalid_syntax_is_a_usage_error(args):
    result = invoke(args)
    assert result.exit_code == 2
    assert "error" in result.stderr.lower()
    assert "not implemented" not in result.stderr.lower()
    assert result.stdout == ""


@pytest.mark.parametrize("name", ["pspec", "powerspec"])
@pytest.mark.parametrize("args", [
    ["upgrade"],
])
def test_installed_aliases_fail_honestly(name, args, tmp_path):
    result = run_process(
        [console(name), *args], tmp_path,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert args[0] in result.stderr
    assert "not implemented" in result.stderr.lower()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("name", ["pspec", "powerspec"])
def test_installed_aliases_report_missing_skill(name, tmp_path):
    result = run_process(
        [console(name), "skill", "pspec-tdd", "--agent", "codex", "--json"], tmp_path,
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

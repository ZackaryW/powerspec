from pathlib import Path
import json

from typer.testing import CliRunner


def invoke(args, *, input=None):
    from powerspec.cli import app

    return CliRunner().invoke(app, args, input=input)


def put(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_root_help_exposes_only_the_canonical_control_plane_and_groups():
    from typer.main import get_command
    from powerspec.cli import app

    result = invoke(["--help"])
    assert result.exit_code == 0
    for command in ("init", "status", "sync", "upgrade", "doctor", "config", "state", "resolve"):
        assert command in result.stdout
    assert "install" not in result.stdout
    command = get_command(app)
    for removed in ("skill", "hook", "flush"):
        assert removed not in command.commands


def test_nested_protocol_and_state_help_is_side_effect_free(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for args in (["resolve", "skill", "--help"], ["resolve", "hook", "--help"], ["state", "clear", "--help"]):
        result = invoke(args)
        assert result.exit_code == 0 and result.stderr == ""
    assert list(tmp_path.iterdir()) == []

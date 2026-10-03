from pathlib import Path
import json

from typer.testing import CliRunner


def invoke(args, *, input=None):
    from powerspec.cli import app

    return CliRunner().invoke(app, args, input=input)


def put(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_root_help_exposes_control_plane_and_groups_but_hides_compatibility_aliases():
    from typer.main import get_command
    from powerspec.cli import app

    result = invoke(["--help"])
    assert result.exit_code == 0
    for command in ("init", "status", "sync", "install", "upgrade", "doctor", "config", "state", "resolve"):
        assert command in result.stdout
    command = get_command(app)
    for hidden in ("skill", "hook", "flush"):
        assert command.commands[hidden].hidden is True


def test_nested_protocol_and_state_help_is_side_effect_free(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for args in (["resolve", "skill", "--help"], ["resolve", "hook", "--help"], ["state", "clear", "--help"]):
        result = invoke(args)
        assert result.exit_code == 0 and result.stderr == ""
    assert list(tmp_path.iterdir()) == []


def test_hidden_skill_alias_matches_resolve_protocol(tmp_path, monkeypatch):
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    put(home / ".codex/skills/example/SKILL.md", "---\nname: example\ndescription: Example.\n---\n")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("CODEX_HOME", str(home / ".codex"))
    monkeypatch.chdir(project)
    old = invoke(["skill", "example", "--agent", "codex", "--json"])
    new = invoke(["resolve", "skill", "example", "--agent", "codex", "--json"])
    assert old.exit_code == new.exit_code == 0
    assert old.stdout == new.stdout == "null\n"


def test_hidden_flush_alias_matches_state_clear(tmp_path, monkeypatch):
    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    put(project / "openspec/.pspec/config.toml", "[vars]\n")
    current = project / "openspec/.pspec/current.toml"
    put(current, '[vars]\nvalue="one"\n')
    monkeypatch.chdir(project)
    grouped = invoke(["state", "clear"])
    put(current, '[vars]\nvalue="one"\n')
    alias = invoke(["flush"])
    assert grouped.exit_code == alias.exit_code == 0
    assert grouped.stdout == alias.stdout

import json
from pathlib import Path

from powerspec.configuration import read_configuration, set_profile
from powerspec.state import read_state


def put(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def setup(tmp_path):
    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    put(
        project / "openspec/.pspec/config.toml",
        '# keep\nprofile = "@builtin/one" # selected\nexclude-profiles=[]\n[vars]\nlanguage="python"\n',
    )
    put(
        project / "openspec/.pspec/current.toml",
        '[vars]\nshared="value"\n[_change.work]\nmode="focused"\n',
    )
    return project


def test_profile_update_and_clear_preserve_other_configuration_and_comments(tmp_path):
    project = setup(tmp_path)
    changed = set_profile(project, "@builtin/two")
    text = changed.path.read_text(encoding="utf-8")
    assert changed.updated and 'profile = "@builtin/two" # selected' in text
    assert '# keep' in text and 'language="python"' in text
    cleared = set_profile(project, None)
    assert cleared.updated and 'profile = "" # selected' in cleared.path.read_text(encoding="utf-8")
    observed = read_configuration(project)
    assert observed.profile is None and observed.variables == {"language": "python"}


def test_state_read_preserves_global_and_change_scopes(tmp_path):
    result = read_state(setup(tmp_path))
    assert result.variables == {"shared": "value"}
    assert result.changes == {"work": {"mode": "focused"}}


def test_config_and_state_show_emit_json(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from powerspec.cli import app

    project = setup(tmp_path)
    monkeypatch.chdir(project)
    config = CliRunner().invoke(app, ["config", "show", "--json"])
    state = CliRunner().invoke(app, ["state", "show", "--json"])
    assert config.exit_code == state.exit_code == 0
    assert json.loads(config.stdout)["variables"] == {"language": "python"}
    assert json.loads(state.stdout)["changes"]["work"] == {"mode": "focused"}


def test_config_edit_reports_missing_editor_without_change(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from powerspec.cli import app

    project = setup(tmp_path)
    path = project / "openspec/.pspec/config.toml"
    before = path.read_bytes()
    monkeypatch.chdir(project)
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.delenv("EDITOR", raising=False)
    result = CliRunner().invoke(app, ["config", "edit"])
    assert result.exit_code == 1 and "VISUAL or EDITOR" in result.stderr
    assert path.read_bytes() == before


def test_config_edit_launches_literal_editor_arguments(tmp_path, monkeypatch):
    import subprocess
    import powerspec.configuration as configuration

    project = setup(tmp_path)
    calls = []
    monkeypatch.setattr(
        configuration.subprocess,
        "run",
        lambda argv, **kwargs: calls.append((argv, kwargs)) or subprocess.CompletedProcess(argv, 0),
    )
    path = configuration.edit_configuration(project, environment={"EDITOR": "editor --wait"})
    assert path == project / "openspec/.pspec/config.toml"
    assert calls == [(["editor", "--wait", str(path)], {"cwd": project.resolve()})]


def test_windows_editor_arguments_remove_grouping_quotes():
    from powerspec.configuration import _editor_argv

    assert _editor_argv(
        '"C:\\Program Files\\Editor\\editor.exe" "C:\\tools\\edit.py" --wait',
        windows=True,
    ) == [
        "C:\\Program Files\\Editor\\editor.exe",
        "C:\\tools\\edit.py",
        "--wait",
    ]

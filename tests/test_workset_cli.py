import json

import pytest
from typer.testing import CliRunner


def invoke(args):
    from powerspec.cli import app
    return CliRunner().invoke(app, ["workset", *args])


@pytest.mark.parametrize("args", [["--help"], ["add", "--help"], ["launch", "--help"]])
def test_workset_help_has_no_effects(args, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = invoke(args)
    assert result.exit_code == 0, result.output
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("extra", [["--store", "x"], ["--keep-source"], ["--repo0=x"], ["--unknown=x"], ["--branch1=x"]])
def test_launch_usage_errors_json(extra):
    result = invoke(["launch", "x", "--branch", "topic", "--json", *extra])
    assert result.exit_code == 2, result.output
    assert json.loads(result.stdout)["stage"] == "arguments"


def test_actual_indexed_cli_dispatch(tmp_path, monkeypatch):
    import powerspec.cli.workset as module
    calls = []
    def launch(*args, **kwargs):
        calls.append((args, kwargs))
        return {"ok": True, "stage": "complete", "members": [], "errors": [], "effects": []}
    monkeypatch.setattr(module, "launch_workset", launch)
    monkeypatch.chdir(tmp_path)
    result = invoke(["launch", "source", "--branch", "shared", "--repo25=a", "--branch25", "own", "--json"])
    assert result.exit_code == 0, result.output
    assert calls[0][0][3] == {25: {"repo": "a", "branch": "own"}}
    assert json.loads(result.stdout)["ok"]


@pytest.mark.parametrize("args", [["launch", "source"], ["add", "source"], ["launch", "--branch", "x"], ["launch", "source", "--branch"]])
def test_missing_required_arguments_still_emit_json(args):
    result = invoke([*args, "--json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["stage"] == "arguments"

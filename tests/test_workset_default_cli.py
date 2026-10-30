import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from powerspec.cli import app
from powerspec.workset_openspec import Member, Workset


class FakeOpenSpec:
    def __init__(self, worksets=None, error=None):
        self.worksets = worksets if worksets is not None else {"poc-ab": Workset("poc-ab", (
            Member("central", Path("/w/central")), Member("server", Path("/w/server"))))}
        self.error = error
        self.calls = []

    def list_worksets(self):
        if self.error:
            raise ValueError(self.error)
        return dict(self.worksets)

    def call(self, *args, **kwargs):
        self.calls.append(args)
        raise AssertionError("defaults must not change OpenSpec")

    publish = append_member = call


@pytest.fixture
def world(tmp_path, monkeypatch):
    import powerspec.cli.workset as cli_workset
    import powerspec.workset_defaults as defaults
    fake = FakeOpenSpec()
    path = tmp_path / ".powerspec/worksets.toml"
    monkeypatch.setattr(cli_workset, "OpenSpec", lambda _cwd: fake)
    monkeypatch.setattr(defaults, "defaults_file", lambda: path)
    monkeypatch.chdir(tmp_path)
    return fake, path


def run(*args):
    return CliRunner().invoke(app, ["workset", "default", *args])


def result_of(*args):
    outcome = run(*args, "--json")
    return outcome.exit_code, json.loads(outcome.stdout)


def test_set_show_repeat_and_clear(world):
    fake, path = world

    assert result_of("poc-ab", "central") == (0, {
        "ok": True, "action": "set", "workset": "poc-ab", "default": "central",
        "path": Path("/w/central").as_posix(), "status": "current"})
    written = path.stat().st_mtime_ns
    assert result_of("poc-ab", "central")[1]["action"] == "unchanged"
    assert path.stat().st_mtime_ns == written
    assert result_of("poc-ab")[1] | {} == {
        "ok": True, "action": "shown", "workset": "poc-ab", "default": "central",
        "path": Path("/w/central").as_posix(), "status": "current"}
    assert result_of("poc-ab", "--clear")[1]["action"] == "cleared"
    assert result_of("poc-ab", "--clear")[1]["action"] == "absent"
    assert result_of("poc-ab")[1]["default"] is None
    assert fake.calls == []


def test_human_output_names_the_default(world):
    outcome = run("poc-ab", "central")
    assert outcome.exit_code == 0
    assert "poc-ab" in outcome.stdout and "central" in outcome.stdout


@pytest.mark.parametrize("args,message", [
    (("missing", "central"), "missing"),
    (("poc-ab", "web"), "central, server"),
    (("poc-ab", "central", "--clear"), "--clear"),
])
def test_invalid_requests_fail_without_writing(world, args, message):
    _, path = world
    code, result = result_of(*args)
    assert code == 1 and not result["ok"]
    assert message in " ".join(result["errors"])
    assert not path.exists()


def test_openspec_failure_is_reported(world):
    fake, path = world
    fake.error = "OpenSpec is required"
    code, result = result_of("poc-ab", "central")
    assert code == 1 and "OpenSpec is required" in result["errors"][0]


@pytest.mark.parametrize("change,reason", [
    (lambda w: w.pop("poc-ab"), "workset removed"),
    (lambda w: w.update({"poc-ab": Workset("poc-ab", (Member("server", Path("/w/server")),))}), "label no longer a member"),
    (lambda w: w.update({"poc-ab": Workset("poc-ab", (Member("central", Path("/w/central")), Member("server", Path("/w/server")), Member("web", Path("/w/web"))))}), "members changed"),
])
def test_show_reports_staleness_with_a_fix(world, change, reason):
    fake, _ = world
    assert result_of("poc-ab", "central")[0] == 0
    change(fake.worksets)

    assert result_of("poc-ab")[1]["status"] == f"stale: {reason}"
    human = run("poc-ab")
    assert reason in human.stdout and "pspec workset default poc-ab" in human.stdout

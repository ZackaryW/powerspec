"""Antigravity hooks: workspace from the payload, one or several projects."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib

import pytest
import typer
from typer.testing import CliRunner

from powerspec.cli import app
from tests.test_hook_input import project  # noqa: F401  (fixture)

AGY = ["resolve", "hook", "sessionStart", "--agent", "antigravity", "--stdin-workspace"]
INTRO = "This session includes several Powerspec projects."
COMMAND = "pspec resolve hook sessionStart --agent antigravity"
ASK = "Ask the user which mode to use."


def consumer_at(root, body):
    """A consumer like the ``project`` fixture, with its own sessionStart body."""
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "--quiet", str(root)], check=True)
    config = root / "openspec/.pspec"
    (config / "profiles").mkdir(parents=True)
    (config / "traits").mkdir()
    from powerspec.resources import builtin_catalog_root
    with builtin_catalog_root() as catalog:
        excluded = [f"@builtin/{p.stem}" for p in (catalog / "profiles").glob("*.toml")
                    if tomllib.loads(p.read_text(encoding="utf-8")).get("global")]
    (config / "config.toml").write_text(
        'profile="@local/t"\nexclude-profiles=' + json.dumps(excluded), encoding="utf-8")
    (config / "profiles/t.toml").write_text('traits=["@local/t"]\n', encoding="utf-8")
    (config / "traits/t.toml").write_text(
        f'hooks=["sessionStart"]\nbody={json.dumps(body)}\n', encoding="utf-8")
    return root


def payload(*paths, **extra):
    return json.dumps({"workspacePaths": [Path(p).as_posix() for p in paths],
                       "conversationId": "c1", "modelName": "auto", **extra})


def agy(monkeypatch, cwd, text):
    monkeypatch.chdir(cwd)
    return CliRunner().invoke(app, AGY, input=text)


def injected(stdout):
    return json.loads(stdout)["injectSteps"][0]["systemMessage"]["systemMessage"]


class Unreadable:
    def read(self, *args):
        raise AssertionError("hook attempted to read stdin")

    readline = read

    def isatty(self):
        raise AssertionError("hook attempted to poll stdin")


def test_payload_workspace_selects_the_consumer_from_a_fixed_host_directory(project, tmp_path, monkeypatch):
    host = tmp_path / "gemini-config"
    host.mkdir()
    result = agy(monkeypatch, host, payload(project, cwd=str(tmp_path), lastUserInput="hi"))
    assert result.exit_code == 0, result.output
    assert injected(result.stdout) == ASK
    assert result.stderr == ""


def test_payload_subdirectory_finds_the_owning_consumer(project, tmp_path, monkeypatch):
    nested = project / "src/deep"
    nested.mkdir(parents=True)
    assert injected(agy(monkeypatch, tmp_path, payload(nested)).stdout) == ASK


@pytest.mark.parametrize("agent", ["codex", "claude"])
def test_payload_option_is_rejected_for_agents_that_never_read_stdin(project, monkeypatch, agent):
    from powerspec.cli.hook import hook
    monkeypatch.chdir(project)
    monkeypatch.setattr(sys, "stdin", Unreadable())
    with pytest.raises(typer.Exit) as raised:
        hook("sessionStart", agent, stdin_workspace=True)
    assert raised.value.exit_code == 1


def test_default_antigravity_invocation_never_touches_stdin(project, monkeypatch, capsys):
    from powerspec.cli.hook import hook
    monkeypatch.chdir(project)
    monkeypatch.setattr(sys, "stdin", Unreadable())
    hook("sessionStart", "antigravity")
    assert injected(capsys.readouterr().out) == ASK


@pytest.mark.parametrize("text", [
    "", "not JSON", "[1]", json.dumps({"workspacePaths": "nope"}),
    json.dumps({"workspacePaths": ["/definitely/missing/dir"]}),
])
def test_unusable_payload_delivers_nothing_without_cwd_fallback(project, monkeypatch, text):
    result = agy(monkeypatch, project, text)
    assert result.exit_code == 0
    assert result.stdout == ""
    assert result.stderr.startswith("Warning:")


def test_malformed_config_in_the_only_workspace_fails(project, tmp_path, monkeypatch):
    (project / "openspec/.pspec/config.toml").write_text("profile=12\n", encoding="utf-8")
    result = agy(monkeypatch, tmp_path, payload(project))
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "config.toml" in result.stderr


def test_interactive_terminal_resolves_from_the_working_directory(project, monkeypatch, capsys):
    from powerspec.cli.hook import hook

    class Terminal:
        def isatty(self):
            return True

        def read(self, *args):
            raise AssertionError("terminal input must not be read")

        readline = read

    monkeypatch.chdir(project)
    monkeypatch.setattr(sys, "stdin", Terminal())
    hook("sessionStart", "antigravity", stdin_workspace=True)
    assert injected(capsys.readouterr().out) == ASK


def test_two_consumers_get_a_project_list_and_no_guidance(tmp_path, monkeypatch):
    api = consumer_at(tmp_path / "api-feature-x", "API rules.")
    web = consumer_at(tmp_path / "web-feature-x", "Web rules.")
    result = agy(monkeypatch, tmp_path, payload(api, web))
    assert result.exit_code == 0, result.output
    text = injected(result.stdout)
    assert text.startswith(INTRO) and COMMAND in text
    assert f"- api-feature-x ({api})" in text and f"- web-feature-x ({web})" in text
    assert "API rules." not in text and "Web rules." not in text and "###" not in text


def test_listed_command_returns_only_that_projects_guidance(tmp_path, monkeypatch):
    consumer_at(tmp_path / "api", "API rules.")
    web = consumer_at(tmp_path / "web", "Web rules.")
    monkeypatch.chdir(web)
    result = CliRunner().invoke(app, COMMAND.split()[1:])
    assert result.exit_code == 0, result.output
    assert injected(result.stdout) == "Web rules."


def test_two_paths_in_one_consumer_deliver_its_guidance_unlabeled(project, monkeypatch, tmp_path):
    (project / "src").mkdir()
    text = injected(agy(monkeypatch, tmp_path, payload(project, project / "src")).stdout)
    assert text == ASK


def test_one_consumer_beside_a_plain_folder_delivers_its_guidance_unlabeled(project, monkeypatch, tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    text = injected(agy(monkeypatch, tmp_path, payload(project, plain)).stdout)
    assert text == ASK


def test_one_malformed_consumer_is_left_out_of_the_list(tmp_path, monkeypatch):
    good = [consumer_at(tmp_path / name, f"{name} rules.") for name in ("good", "fine")]
    bad = consumer_at(tmp_path / "bad", "Bad rules.")
    (bad / "openspec/.pspec/config.toml").write_text("profile=12\n", encoding="utf-8")
    result = agy(monkeypatch, tmp_path, payload(bad, *good))
    assert result.exit_code == 0
    text = injected(result.stdout)
    assert f"- good ({good[0]})" in text and f"- fine ({good[1]})" in text
    assert f"- bad (" not in text and str(bad) in result.stderr


def test_every_consumer_failing_exits_nonzero(tmp_path, monkeypatch):
    roots = [consumer_at(tmp_path / name, name) for name in ("one", "two")]
    for root in roots:
        (root / "openspec/.pspec/config.toml").write_text("profile=12\n", encoding="utf-8")
    result = agy(monkeypatch, tmp_path, payload(*roots))
    assert result.exit_code == 1 and result.stdout == ""


def test_missing_listed_path_is_skipped(project, monkeypatch, tmp_path):
    missing = tmp_path / "gone"
    result = agy(monkeypatch, tmp_path, payload(missing, project))
    assert result.exit_code == 0
    assert ASK in injected(result.stdout)
    assert missing.as_posix() in result.stderr.replace("\\", "/")


def test_seven_project_workset_delivers_no_guidance_bodies(tmp_path, monkeypatch):
    body = "Rule. " * 1000  # About the 6,000-character sessionStart guidance of a real consumer.
    roots = [consumer_at(tmp_path / f"repo-{index}", body) for index in range(7)]
    text = injected(agy(monkeypatch, tmp_path, payload(*roots)).stdout)
    assert text.count("- repo-") == 7
    assert "Rule." not in text and len(text) < 2000


def test_real_antigravity_hook_exits_with_the_pipe_left_open(project, tmp_path):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    host = tmp_path / "host"
    host.mkdir()
    for text in (payload(project).encode(), b""):
        child = subprocess.Popen(
            [sys.executable, "-c", "from powerspec.cli import main; main()", *AGY],
            cwd=host, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        try:
            child.stdin.write(text)
            child.stdin.flush()
            child.wait(timeout=5)
            assert not child.stdin.closed and child.returncode == 0
            output = child.stdout.read().decode()
            if text:
                assert injected(output) == ASK
            else:
                assert output == ""
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=5)
            for stream in (child.stdin, child.stdout, child.stderr):
                stream.close()

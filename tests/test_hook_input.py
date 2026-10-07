"""Exercise hook input at the command boundary, including a pipe without EOF."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import tomllib

import pytest
from typer.testing import CliRunner

from powerspec.cli import app


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    subprocess.run(["git", "init", "--quiet", str(root)], check=True)
    config = root / "openspec/.pspec"
    (config / "profiles").mkdir(parents=True)
    (config / "traits").mkdir()
    # Exclude bundled globals so this subprocess fixture has no optional probes.
    from powerspec.resources import builtin_catalog_root
    with builtin_catalog_root() as catalog:
        excluded = [f"@builtin/{p.stem}" for p in (catalog / "profiles").glob("*.toml")
                    if tomllib.loads(p.read_text(encoding="utf-8")).get("global")]
    (config / "config.toml").write_text(
        'profile="@local/input-test"\nexclude-profiles=' + json.dumps(excluded), encoding="utf-8")
    (config / "profiles/input-test.toml").write_text(
        'traits=["@local/input-test"]\n', encoding="utf-8")
    (config / "traits/input-test.toml").write_text(
        'hooks=["sessionStart", "afterCompaction"]\n'
        'body="Ask the user which mode to use."\n', encoding="utf-8")
    return root


def assert_guidance(output):
    assert json.loads(output) == {"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "Ask the user which mode to use.",
    }}


def test_mixed_dynamic_unknown_hook_json_and_separate_diagnostic(project, monkeypatch):
    from powerspec.catalog import MetadataUnavailable
    from powerspec.sources import SaucepanSources
    config = project / 'openspec/.pspec'
    skill = config / 'skills/dynamic'
    skill.mkdir(parents=True)
    (skill / 'SKILL.md').write_text('---\nname: dynamic\n---\n')
    (skill / 'pspec.toml').write_text('version=2\nentry="SKILL.md"')
    (config / 'profiles/input-test.toml').write_text(
        'traits=["@local/input-test"]\nskills=["@local/dynamic", "remote/*"]\n'
        '[[source]]\nid="remote"\nprovider="git"\norigin="https://example.test/tools"\nreference="main"')
    (config / 'traits/input-test.toml').write_text(
        'hooks=["sessionStart", "afterCompaction"]\nbody="Use <skill:dynamic> and <skill:remote-helper>."')
    calls = []
    def unavailable(self, *args, **kwargs):
        calls.append(kwargs)
        raise MetadataUnavailable('service unavailable')
    monkeypatch.setattr(SaucepanSources, 'lookup', unavailable)
    monkeypatch.setattr(SaucepanSources, 'acquire', lambda *a, **k: pytest.fail('acquire'))
    monkeypatch.chdir(project)
    result = CliRunner().invoke(app, ['resolve', 'hook', 'sessionStart', '--agent', 'codex'])
    assert result.exit_code == 0, result.output
    guidance = json.loads(result.stdout)['hookSpecificOutput']['additionalContext']
    assert 'Skills requiring dynamic resolution: dynamic\n' in guidance
    assert 'Skill metadata unavailable: remote-helper\n' in guidance
    assert guidance.endswith('Use dynamic and remote-helper.')
    assert result.stderr == 'Warning: service unavailable\n'
    assert len(calls) == 1 and 'deadline' in calls[0]


@pytest.mark.parametrize("content", ["", "not JSON", '{"cwd":"/wrong/repo"}'])
def test_hook_ignores_input_and_does_not_write_state(project, monkeypatch, content):
    monkeypatch.chdir(project)
    before = {p.relative_to(project): p.read_bytes()
              for p in (project / "openspec").rglob("*") if p.is_file()}
    result = CliRunner().invoke(app, ["resolve", "hook", "sessionStart", "--agent", "codex"],
                                input=content)
    assert result.exit_code == 0, result.output
    assert_guidance(result.stdout)
    assert result.stderr == ""
    assert before == {p.relative_to(project): p.read_bytes()
                      for p in (project / "openspec").rglob("*") if p.is_file()}


def test_hook_never_touches_stdin(project, monkeypatch, capsys):
    from powerspec.cli.hook import hook
    class Unreadable:
        def read(self, *args):
            raise AssertionError("hook attempted to read stdin")
        readline = read
        def isatty(self):
            raise AssertionError("hook attempted to poll stdin")
    monkeypatch.chdir(project)
    monkeypatch.setattr(sys, "stdin", Unreadable())
    hook("sessionStart", "codex")
    assert_guidance(capsys.readouterr().out)


@pytest.mark.parametrize("event,agent", [("unknown", "codex"), ("sessionStart", "unknown")])
def test_invalid_mapping_has_diagnostic_without_input(project, monkeypatch, event, agent):
    monkeypatch.chdir(project)
    result = CliRunner().invoke(app, ["resolve", "hook", event, "--agent", agent])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "unsupported logical hook" in result.stderr or "no verified" in result.stderr


@pytest.mark.parametrize("case", ["no-consumer", "no-match", "malformed"])
def test_hook_empty_and_error_outcomes_without_input(project, monkeypatch, tmp_path, case):
    if case == "no-consumer":
        monkeypatch.chdir(tmp_path)
    else:
        monkeypatch.chdir(project)
        config = project / "openspec/.pspec"
        if case == "no-match":
            (config / "traits/input-test.toml").write_text(
                'hooks=["afterCompaction"]\nbody="not selected"\nwhen="missing()"')
        else:
            (config / "config.toml").write_text("profile=12\n")
    result = CliRunner().invoke(app, ["resolve", "hook", "sessionStart", "--agent", "codex"])
    assert result.stdout == ""
    assert result.exit_code == (1 if case == "malformed" else 0)
    if case == "malformed":
        assert "config.toml" in result.stderr
    else:
        assert result.stderr == ""


@pytest.mark.parametrize("agent", ["codex", "claude"])
@pytest.mark.parametrize("event", ["sessionStart", "afterCompaction"])
def test_real_hook_exits_with_stdin_left_open(project, agent, event):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    started = time.monotonic()
    child = subprocess.Popen(
        [sys.executable, "-c", "from powerspec.cli import main; main()",
         "resolve", "hook", event, "--agent", agent],
        cwd=project, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True,
    )
    try:
        # Do not communicate(): it closes stdin and would conceal this bug.
        child.wait(timeout=5)
        assert not child.stdin.closed
        assert child.returncode == 0, child.stderr.read()
        assert_guidance(child.stdout.read())
        assert child.stderr.read() == ""
        print(f"{agent}/{event}: {time.monotonic() - started:.3f}s (stdin open)")
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)
        child.stdin.close()
        child.stdout.close()
        child.stderr.close()

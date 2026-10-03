from contextlib import contextmanager
from functools import partial
import importlib
import subprocess

import pytest
from typer.testing import CliRunner

from powerspec.catalog import ConfigurationError
from powerspec.cli import app
from powerspec.installation import install_consumer
from powerspec.sources import SourceBinding
from test_installation import setup, put
from test_initialization import bootstrap


@pytest.fixture
def environment(tmp_path, monkeypatch):
    project, builtin, remote = setup(tmp_path)
    subprocess.run(["git", "init", "--quiet", str(project)], check=True)
    calls = []

    class Sources:
        def ensure(self, identity, recipe):
            calls.append(identity)
            return SourceBinding(identity, recipe["origin"], recipe["reference"], "a" * 40, "s", "a", remote)

    @contextmanager
    def resources():
        yield builtin

    import powerspec.workspace as workspace
    import powerspec.initialization as initialization
    module = importlib.import_module("powerspec.cli.init")
    monkeypatch.setattr(workspace, "builtin_catalog_root", resources)
    monkeypatch.setattr(workspace, "SaucepanSources", lambda **_: Sources())
    monkeypatch.setattr(initialization, "bootstrap_openspec", bootstrap)
    monkeypatch.setattr(module, "install_consumer", partial(
        install_consumer, home=tmp_path / "home", registry=tmp_path / "registry", source_store=Sources()
    ), raising=False)
    monkeypatch.chdir(project)
    return project, builtin, remote, calls


def test_init_provisions_and_reuses_agent_assets(environment, tmp_path):
    project, _, _, calls = environment
    for expected in ("installed", "reused"):
        result = CliRunner().invoke(app, ["init", "--agent", "codex"])
        assert result.exit_code == 0, result.output
        assert expected in result.stdout
        assert "Initialization complete" in result.stdout
    assert (tmp_path / "home/.codex/skills/example/SKILL.md").is_file()
    assert not (project / ".agents/skills").exists()
    assert calls == ["tools", "tools"]


def test_plain_init_prepares_sources_without_agent(environment, tmp_path):
    project, _, _, calls = environment
    result = CliRunner().invoke(app, ["init"])
    assert result.exit_code == 0, result.output
    assert calls == ["tools"]
    assert "init --agent" in result.stdout
    assert not (tmp_path / "home").exists()


def test_fresh_global_init_preserves_profile_scope(environment, tmp_path):
    project, builtin, _, _ = environment
    config = project / "openspec/.pspec/config.toml"
    config.unlink()
    profile = builtin / "profiles/main.toml"
    profile.write_text('global=true\n' + profile.read_text().replace('scope="user"', 'scope="project"'))
    result = CliRunner().invoke(app, ["init", "--agent", "codex"])
    assert result.exit_code == 0, result.output
    assert config.read_text() == "[vars]\n"
    assert (project / ".agents/skills/example/SKILL.md").is_file()
    assert not (tmp_path / "home/.codex/skills/example").exists()


def test_init_from_nested_consumer_sets_up_git_root(environment, monkeypatch, tmp_path):
    project, _, _, _ = environment
    nested = project / "nested"
    put(nested / "openspec/.pspec/config.toml", 'profile="@builtin/nonexistent"\n')
    monkeypatch.chdir(nested)
    result = CliRunner().invoke(app, ["init", "--agent", "codex"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "home/.codex/skills/example/SKILL.md").is_file()


def test_invalid_agent_precedes_consumer_writes(environment):
    project, _, _, calls = environment
    result = CliRunner().invoke(app, ["init", "--agent", "nonexistent"])
    assert result.exit_code != 0
    assert not (project / "openspec/config.yaml").exists()
    assert not calls


def test_init_source_failure_preserves_configuration(environment, monkeypatch):
    project, _, _, _ = environment
    module = importlib.import_module("powerspec.cli.init")

    def fail(*args, **kwargs):
        raise ConfigurationError("source unavailable")

    monkeypatch.setattr(module, "install_consumer", fail)
    config = project / "openspec/.pspec/config.toml"
    before = config.read_bytes()
    result = CliRunner().invoke(app, ["init", "--agent", "codex"])
    assert result.exit_code == 1
    assert "source unavailable" in result.stderr
    assert "Initialization complete" not in result.stdout
    assert "rerun" in result.stderr
    assert config.read_bytes() == before
    assert (project / "openspec/config.yaml").is_file()


def test_partial_agent_failure_keeps_successes(environment, tmp_path):
    _, _, remote, _ = environment
    put(remote / "skills/second/SKILL.md", "---\nname: second\ndescription: Second.\n---\n")
    foreign = tmp_path / "home/.codex/skills/example/SKILL.md"
    put(foreign, "---\nname: example\n---\nUser content\n")
    result = CliRunner().invoke(app, ["init", "--agent", "codex"])
    assert result.exit_code == 1
    assert "Initialization complete" not in result.stdout
    assert "rerun" in result.stderr
    assert foreign.read_text().endswith("User content\n")
    assert (tmp_path / "home/.codex/skills/second/SKILL.md").is_file()


def test_install_is_no_longer_a_command():
    result = CliRunner().invoke(app, ["install", "--help"])
    assert result.exit_code == 2

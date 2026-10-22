import importlib

import pytest
from typer.testing import CliRunner

from powerspec.catalog import ConfigurationError
from powerspec.cli import app
from test_bootstrap_lifecycle import environment


@pytest.mark.parametrize('arguments', [[], ['--agent', 'codex']])
def test_init_reports_stages_to_stderr_without_changing_stdout(environment, arguments):
    result = CliRunner().invoke(app, ['init', *arguments])
    assert result.exit_code == 0, result.output
    assert 'Starting: Establishing consumer' in result.stderr
    assert 'Resolving source: tools (main)' in result.stderr
    if arguments:
        assert 'Checking skill 1/1: example' in result.stderr
        assert 'Reconciling codex hooks' in result.stderr
    assert 'Starting:' not in result.stdout
    assert 'Initialization complete' in result.stdout


def test_setup_failure_has_stage_elapsed_and_retry_context(environment, monkeypatch):
    module = importlib.import_module('powerspec.cli.init')
    def fail(*args, **kwargs):
        raise ConfigurationError('source tools: timeout; mutation may have committed')
    monkeypatch.setattr(module, 'install_consumer', fail)
    result = CliRunner().invoke(app, ['init', '--agent', 'codex'])
    assert result.exit_code == 1
    assert 'failed: Preparing sources and agent assets (' in result.stderr
    assert 'timeout; mutation may have committed' in result.stderr
    assert 'rerun pspec init' in result.stderr
    assert 'Initialization complete' not in result.stdout


def test_skill_conflict_is_observed_before_next_skill(environment, tmp_path, monkeypatch):
    from powerspec import provisioning
    from powerspec.installation import install_consumer
    from powerspec.progress import lifecycle_progress
    from test_installation import put
    project, _, remote, _ = environment
    put(remote / 'skills/second/SKILL.md', '---\nname: second\ndescription: Second.\n---\n')
    foreign = tmp_path / 'home/.codex/skills/example/SKILL.md'
    put(foreign, '---\nname: example\n---\nUser content\n')
    events = []
    original = provisioning.inspect_asset
    inspected_second = []
    def inspect(asset, **kwargs):
        if 'second' in str(asset.source):
            assert any(event.state == 'failed' and 'example' in event.label for event in events)
            inspected_second.append(True)
        return original(asset, **kwargs)
    monkeypatch.setattr(provisioning, 'inspect_asset', inspect)
    with lifecycle_progress(events.append):
        result = install_consumer(project, agent='codex', home=tmp_path / 'home', registry=tmp_path / 'registry')
    assert not result.ok and inspected_second
    assert foreign.read_text().endswith('User content\n')
    assert any(event.state == 'installed' and 'second' in event.label for event in events)

from copy import deepcopy
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from powerspec.cli import app
from powerspec.hooks import native_document
from test_bootstrap_lifecycle import environment
from test_installation import put


@pytest.mark.parametrize('agent', [None, 'codex'])
def test_force_refreshes_sources_with_optional_agent(environment, tmp_path, agent):
    project, _, _, calls = environment
    arguments = ['init', '--force'] + (['--agent', agent] if agent else [])
    result = CliRunner().invoke(app, arguments)
    assert result.exit_code == 0, result.output
    assert calls == ['refresh:tools']
    assert 'Initialization complete' in result.stdout
    assert (tmp_path / 'home/.codex/skills/example/SKILL.md').exists() is bool(agent)
    assert (tmp_path / 'home/.codex/hooks.json').exists() is bool(agent)


def test_force_authorizes_default_manager_only_at_init_boundary(environment, monkeypatch):
    import powerspec.workspace as workspace
    factory = workspace.SaucepanSources
    seen = []
    def source_store(**options):
        seen.append(options)
        return factory(**options)
    monkeypatch.setattr(workspace, 'SaucepanSources', source_store)
    assert CliRunner().invoke(app, ['init', '--force']).exit_code == 0
    assert seen == [dict(manage_binary=True, migrate_unmanaged=True)]


def test_force_replaces_differing_skills_recoverably(environment, tmp_path):
    foreign = tmp_path / 'home/.codex/skills/example/SKILL.md'
    put(foreign, '---\nname: example\ndescription: User.\n---\nUser content\n')
    result = CliRunner().invoke(app, ['init', '--agent', 'codex', '--force'])
    assert result.exit_code == 0, result.output
    assert 'updated: ' in result.stdout and 'ZuAT skill operation:' in result.stdout
    assert 'User content' not in foreign.read_text()


def test_force_repairs_matching_hook_receipt_and_reports_operation(environment, tmp_path, monkeypatch):
    import powerspec.provisioning as provisioning
    current = native_document('codex')
    legacy = deepcopy(current)
    legacy['hooks']['SessionStart'][0]['matcher'] = 'startup|resume|clear'
    with monkeypatch.context() as patch:
        patch.setattr(provisioning, 'native_document', lambda _: legacy)
        assert CliRunner().invoke(app, ['init', '--agent', 'codex']).exit_code == 0
    native = tmp_path / 'home/.codex/hooks.json'
    native.write_text(json.dumps({'unrelated': True, **current}, indent=3))
    before = native.read_bytes(), native.stat().st_mtime_ns
    assert CliRunner().invoke(app, ['init', '--agent', 'codex']).exit_code == 1
    result = CliRunner().invoke(app, ['init', '--agent', 'codex', '--force'])
    assert result.exit_code == 0, result.output
    assert 'ZuAT hook operation:' in result.stdout
    assert (native.read_bytes(), native.stat().st_mtime_ns) == before


def test_invalid_agent_with_force_has_no_effects(environment):
    project, _, _, calls = environment
    result = CliRunner().invoke(app, ['init', '--agent', 'invalid', '--force'])
    assert result.exit_code != 0 and not calls
    assert not (project / 'openspec/config.yaml').exists()


def test_init_help_lists_force_recovery_scope():
    result = CliRunner().invoke(app, ['init', '--help'], color=False)
    assert result.exit_code == 0
    assert '--force' in result.stdout
    assert all(word in result.stdout.lower() for word in ('refresh', 'migration', 'hook', 'replace'))
    assert '--scope' in result.stdout and all(word in result.stdout for word in ('local', 'global', 'all'))


@pytest.fixture
def conflicting(environment, tmp_path):
    foreign = tmp_path / 'home/.codex/skills/example/SKILL.md'
    put(foreign, '---\nname: example\ndescription: User.\n---\nUser content\n')
    return foreign


def test_interactive_init_replaces_conflicts_after_one_confirmation(conflicting, monkeypatch):
    monkeypatch.setattr('powerspec.cli.init._interactive', lambda: True)
    result = CliRunner().invoke(app, ['init', '--agent', 'codex'], input='y\n')
    assert result.exit_code == 0, result.output
    assert result.stderr.count('Replace them?') == 1
    assert 'example (codex/user)' in result.stderr
    assert 'ZuAT skill operation:' in result.stdout and 'Initialization complete' in result.stdout
    assert 'User content' not in conflicting.read_text()


def test_declined_confirmation_preserves_conflicts_and_names_remedy(conflicting, monkeypatch):
    monkeypatch.setattr('powerspec.cli.init._interactive', lambda: True)
    before = conflicting.read_bytes()
    result = CliRunner().invoke(app, ['init', '--agent', 'codex'], input='n\n')
    assert result.exit_code == 1
    assert conflicting.read_bytes() == before
    assert 'Error: agent provisioning incomplete; replace conflicting skills with pspec init --agent codex --force' in result.stderr


def test_non_interactive_init_never_prompts(conflicting, monkeypatch):
    monkeypatch.setattr('powerspec.cli.init._interactive', lambda: False)
    before = conflicting.read_bytes()
    result = CliRunner().invoke(app, ['init', '--agent', 'codex'])
    assert result.exit_code == 1
    assert 'Replace them?' not in result.output
    assert conflicting.read_bytes() == before
    assert 'pspec init --agent codex --force' in result.stderr

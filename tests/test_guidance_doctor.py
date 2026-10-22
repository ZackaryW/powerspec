from contextlib import contextmanager
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from powerspec.cli import app
from powerspec.doctoring import doctor_consumer
from powerspec.hooks import native_document
from powerspec.utils.inspection import ExecutableResult


@pytest.fixture
def delivery(tmp_path, monkeypatch):
    project = tmp_path / 'project'
    (project / '.git').mkdir(parents=True)
    config = project / 'openspec/.pspec/config.toml'
    config.parent.mkdir(parents=True)
    config.write_text('[vars]\n')
    root = tmp_path / 'catalog'
    authored = Path(__file__).resolve().parents[1] / '.pspec'
    for name in ('profiles/zmem-lifecycle.toml', 'contexts/zmem-lifecycle.toml',
                 'contexts/incremental-checkpoints.toml', 'traits/zmem-lifecycle.toml',
                 'guidance/zmem-lifecycle.md'):
        dest = root / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((authored / name).read_bytes())
    # Other authoring/commit rules are unrelated to this fixture's diagnostics.
    (root / 'contexts/incremental-checkpoints.toml').write_text('')
    body = (root / 'guidance/zmem-lifecycle.md').read_text()
    import re
    rendered = re.sub(r'<skill:([^>]+)>', r'\1', body).strip()
    from ruamel.yaml import YAML
    target = project / 'openspec/config.yaml'
    with target.open('w', encoding='utf-8') as stream:
        YAML().dump({'schema': 'spec-driven', 'context': rendered}, stream)
    @contextmanager
    def builtin():
        yield root
    monkeypatch.setattr('powerspec.workspace.builtin_catalog_root', builtin)
    home = tmp_path / 'home'
    codex = home / '.codex'
    codex.mkdir(parents=True)
    (codex / 'hooks.json').write_text(json.dumps(native_document('codex')))
    monkeypatch.setenv('CODEX_HOME', str(codex))
    monkeypatch.setenv('POWERSPEC_SAUCEPAN', str(home / 'standalone'))
    calls = []
    def inspect(argv, **kwargs):
        calls.append(argv)
        if argv[0] == 'pspec':
            envelope = {'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': rendered}}
            return ExecutableResult('ok', 'pspec', 0, json.dumps(envelope), 'Warning: source metadata unavailable')
        version = '1.14.3' if argv[0] == 'openspec' else '0.10.0'
        return ExecutableResult('ok', argv[0], 0, version, '', version)
    monkeypatch.setattr('powerspec.doctoring.inspect_executable', inspect)
    monkeypatch.chdir(project)
    return project, codex, calls


def test_cli_reports_generation_but_not_host_receipt(delivery):
    result = CliRunner().invoke(app, ['doctor', '--agent', 'codex', '--json'])
    assert result.exit_code == 0, result.output
    checks = {item['name']: item for item in json.loads(result.stdout)['checks']}
    assert checks['guidance-selection']['status'] == 'ok'
    assert checks['guidance-context']['status'] == 'ok'
    assert checks['guidance-sessionStart']['status'] == 'ok'
    assert checks['guidance-afterCompaction']['status'] == 'ok'
    assert checks['guidance-host-receipt']['status'] == 'warning'
    assert 'unverified' in checks['guidance-host-receipt']['detail']
    assert 'source metadata unavailable' in checks['guidance-sessionStart']['detail']


def test_disabled_hook_fails_without_changing_settings(delivery):
    project, codex, _ = delivery
    key = f'{codex / "hooks.json"}:session_start:0:0'
    settings = codex / 'config.toml'
    from tomlkit import dumps
    text = dumps({'hooks': {'state': {key: {'enabled': False}}}})
    settings.write_text(text)
    result = doctor_consumer(project, agent='codex')
    assert not result.ok
    assert any(item.status == 'failed' and 'disabled' in item.detail for item in result.checks)
    assert settings.read_text() == text


def test_missing_registration_and_stale_context_are_failures(delivery):
    project, codex, _ = delivery
    (codex / 'hooks.json').unlink()
    (project / 'openspec/config.yaml').write_text('schema: spec-driven\n')
    result = doctor_consumer(project, agent='codex')
    failed = {item.name for item in result.checks if item.status == 'failed'}
    assert {'guidance-context', 'hooks-sessionStart', 'hooks-afterCompaction'} <= failed
    assert not (codex / 'hooks.json').exists()


def test_invalid_agent_fails_before_probes(delivery):
    _, _, calls = delivery
    result = CliRunner().invoke(app, ['doctor', '--agent', 'unknown'])
    assert result.exit_code != 0
    assert not calls


@pytest.mark.parametrize('contents', ['{', '[]', '{"hooks":{"SessionStart":{}}}'])
def test_malformed_registration_is_reported(delivery, contents):
    project, codex, _ = delivery
    path = codex / 'hooks.json'
    path.write_text(contents)
    result = doctor_consumer(project, agent='codex')
    assert not result.ok
    assert any(item.name == 'hooks-sessionStart' and item.status == 'failed' for item in result.checks)
    assert path.read_text() == contents


def test_claude_user_disable_and_home_override(delivery, monkeypatch):
    project, codex, _ = delivery
    claude = codex.parent / 'custom-claude'
    claude.mkdir()
    document = native_document('claude')
    document['disableAllHooks'] = True
    path = claude / 'settings.json'
    path.write_text(json.dumps(document))
    before = path.read_bytes()
    monkeypatch.setenv('CLAUDE_CONFIG_DIR', str(claude))
    result = doctor_consumer(project, agent='claude')
    assert not result.ok
    assert any(item.name == 'hooks-settings' and item.status == 'failed' for item in result.checks)
    assert path.read_bytes() == before


def test_exclusion_is_not_a_missing_policy_failure(delivery):
    project, _, _ = delivery
    (project / 'openspec/.pspec/config.toml').write_text('exclude-profiles=["@builtin/zmem-lifecycle"]\n')
    (project / 'openspec/config.yaml').write_text('schema: spec-driven\n')
    result = doctor_consumer(project, agent='codex')
    assert result.ok
    assert 'not selected' in next(item.detail for item in result.checks if item.name == 'guidance-selection')


@pytest.mark.parametrize('output', ['not json', '{}', '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"stale"}}'])
def test_invalid_or_stale_resolver_output_fails(delivery, monkeypatch, output):
    project, _, _ = delivery
    from powerspec import doctoring
    previous = doctoring.inspect_executable
    def inspect(argv, **kwargs):
        return ExecutableResult('ok', 'pspec', 0, output) if argv[0] == 'pspec' else previous(argv, **kwargs)
    monkeypatch.setattr(doctoring, 'inspect_executable', inspect)
    result = doctor_consumer(project, agent='codex')
    assert not result.ok
    assert all(item.status == 'failed' for item in result.checks if item.name.startswith('guidance-') and item.name.endswith(('sessionStart', 'afterCompaction')))


def test_timed_out_generation_is_not_delivery(delivery, monkeypatch):
    project, _, calls = delivery
    from powerspec import doctoring
    previous = doctoring.inspect_executable
    def inspect(argv, **kwargs):
        if argv[0] == 'pspec':
            assert kwargs['timeout'] == 5
            return ExecutableResult('timeout')
        return previous(argv, **kwargs)
    monkeypatch.setattr(doctoring, 'inspect_executable', inspect)
    result = doctor_consumer(project, agent='codex')
    assert not result.ok
    assert any('timeout' in item.detail for item in result.checks)

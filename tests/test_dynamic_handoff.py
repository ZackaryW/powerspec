"""Automated invocation-chain evidence; this does not simulate agent adherence."""
from contextlib import contextmanager
import importlib
import json
import shutil

from typer.testing import CliRunner
from powerspec.catalog import MetadataUnavailable
from powerspec.cli import app
from powerspec.resources import builtin_catalog_root
from powerspec.sources import SaucepanSources, SourceBinding
from test_skill_cli import put


def test_sync_hook_native_selection_pending_and_rerun(tmp_path, monkeypatch):
    project = tmp_path / 'project'
    (project / '.git').mkdir(parents=True)
    root = tmp_path / 'catalog'
    remote = tmp_path / 'remote'
    put(project / 'openspec/.pspec/config.toml', 'profile="@builtin/main"')
    target = put(project / 'openspec/config.yaml', 'schema: spec-driven\ncontext: Keep my text\n')
    put(root / 'profiles/main.toml', 'contexts=["@builtin/guide"]\ntraits=["@builtin/guide"]\n'
        'skills=["@builtin/dynamic", "@builtin/openspec-explore", "remote/skills/*"]\n'
        '[[source]]\nid="remote"\nprovider="git"\norigin="https://example.test/tools"\nreference="main"')
    put(root / 'contexts/guide.toml', '[[attach.context]]\nbody="Use <skill:dynamic> or <skill:openspec-explore> when appropriate."')
    put(root / 'traits/guide.toml', 'hooks=["sessionStart", "afterCompaction"]\n'
        'body="Use <skill:dynamic>, <skill:openspec-explore>, and <skill:remote-helper> when appropriate."')
    with builtin_catalog_root() as bundled:
        shutil.copytree(bundled / 'skills/openspec-explore', root / 'skills/openspec-explore')
    dynamic = root / 'skills/dynamic'
    put(dynamic / 'SKILL.md', '---\nname: dynamic\n---\n\nUse <answer>.\n')
    put(dynamic / 'pspec.toml', 'version=2\nentry="SKILL.md"\n[[input]]\nid="answer"\ntype="string"\n'
        '[input.parser]\ntype="prompt"\nprompt="Which answer?"')
    put(remote / 'skills/helper/SKILL.md', '---\nname: remote-helper\n---\n')
    selected = tmp_path / 'native plugin/selected'
    shutil.copytree(dynamic, selected)
    other = tmp_path / 'home/.codex/skills/dynamic'
    put(other / 'SKILL.md', '---\nname: dynamic\n---\nWrong native copy')
    @contextmanager
    def resources():
        yield root
    for module in ('powerspec.workspace', 'powerspec.cli.hook', 'powerspec.cli.skill'):
        monkeypatch.setattr(importlib.import_module(module), 'builtin_catalog_root', resources)
    monkeypatch.setenv('HOME', str(tmp_path / 'home'))
    monkeypatch.setenv('USERPROFILE', str(tmp_path / 'home'))
    monkeypatch.setenv('CODEX_HOME', str(tmp_path / 'home/.codex'))
    monkeypatch.chdir(project)
    monkeypatch.setattr(SaucepanSources, 'ensure', lambda *a, **k: SourceBinding(
        'remote', 'https://example.test/tools', 'main', 'a' * 40, 's', 'a', remote))
    def unavailable(*args, **kwargs):
        raise MetadataUnavailable('remote unavailable')
    monkeypatch.setattr(SaucepanSources, 'lookup', unavailable)
    runner = CliRunner()
    sync = runner.invoke(app, ['sync'])
    assert sync.exit_code == 0, sync.output
    assert 'Skills requiring dynamic resolution: dynamic' in target.read_text()
    assert 'Keep my text' in target.read_text()
    before = target.read_bytes()
    assert runner.invoke(app, ['sync']).exit_code == 0
    assert target.read_bytes() == before
    hook = runner.invoke(app, ['resolve', 'hook', 'afterCompaction', '--agent', 'codex'])
    assert hook.exit_code == 0, hook.output
    body = json.loads(hook.stdout)['hookSpecificOutput']['additionalContext']
    assert 'Skills requiring dynamic resolution: dynamic' in body
    assert 'Skill metadata unavailable:' in body and 'remote-helper' in body
    ordinary = runner.invoke(app, ['resolve', 'skill', '--path', str(root / 'skills/openspec-explore'), '--agent', 'codex'])
    assert ordinary.stdout.strip() == 'null'
    args = ['resolve', 'skill', '--path', str(selected), '--agent', 'codex', '--change', 'one', '--json']
    pending = runner.invoke(app, args)
    assert pending.exit_code == 0, pending.output
    assert json.loads(pending.stdout)['status'] == 'pending'
    put(project / 'openspec/.pspec/current.toml', '[_change.one]\nanswer="confirmed"')
    resolved = runner.invoke(app, args)
    assert resolved.exit_code == 0, resolved.output
    payload = json.loads(resolved.stdout)
    assert payload['skill_path'] == str(selected.resolve())
    assert 'Use confirmed.' in payload['content']
    assert other.joinpath('SKILL.md').read_text().endswith('Wrong native copy')

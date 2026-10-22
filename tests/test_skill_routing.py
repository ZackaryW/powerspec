"""Observable routing protocol and files; not a simulation of agent adherence."""
import json
from pathlib import Path
import tomllib

import pytest
from typer.testing import CliRunner

from powerspec.cli import app
from powerspec.resources import builtin_catalog_root
from test_catalog_skill_cli import consumer, run
from test_skill_cli import put


@pytest.mark.parametrize('agent', ['codex', 'claude'])
def test_compact_reminder_selection_growth_and_no_prefetch(tmp_path, monkeypatch, agent):
    project, root = consumer(tmp_path)
    profile = root / 'profiles/scenarios.toml'
    profile.write_text(profile.read_text().replace('traits=[', 'traits=["@builtin/skill-bootstrap",'))
    calls = []
    import powerspec.catalog_skills as feature
    original = feature.resolve_catalog_skill
    def tracked(*args, **kwargs):
        calls.append(args[1])
        return original(*args, **kwargs)
    monkeypatch.setattr('powerspec.cli.skill.resolve_catalog_skill', tracked)
    monkeypatch.chdir(project)
    runner = CliRunner()
    def hook(event):
        result = runner.invoke(app, ['resolve','hook',event,'--agent',agent])
        assert result.exit_code == 0 and result.stderr == '', result.output
        return json.loads(result.stdout)['hookSpecificOutput']['additionalContext']
    with builtin_catalog_root() as builtin:
        trait = tomllib.loads((builtin / 'traits/skill-bootstrap.toml').read_text())
    assert trait['body'].strip()  # Packaged resource must actually supply a reminder.
    reminder = trait['body'].replace('<skill:pspec-skill-bootstrap>', 'pspec-skill-bootstrap').strip()
    rule = (root / 'guidance/scenarios.md').read_text()
    expected = reminder + '\n\n' + rule
    assert hook('sessionStart') == expected
    assert hook('afterCompaction') == expected
    assert calls == []
    put(root / 'skills/more/SKILL.md', '---\nname: more\ndescription: UNUSED-DESCRIPTION\n---\nUNUSED-PROCEDURE')
    profile.write_text(profile.read_text().replace('"@local/c"', '"@local/c", "@local/more"'))
    assert hook('sessionStart') == expected
    # Removing bootstrap selection leaves its trait inert and preserves scenario rules.
    profile.write_text(profile.read_text().replace('skills=["@builtin/pspec-skill-bootstrap"]', 'skills=[]'))
    assert hook('sessionStart') == rule
    assert calls == []


def test_scenarios_retrieve_one_at_a_time_and_compaction_does_not_prefetch(tmp_path, monkeypatch):
    from powerspec.workspace import open_workspace
    from powerspec.provisioning import plan_skills, provision_skills
    from test_skill_resolution import skill as dynamic
    import powerspec.cli.skill as cli_skill
    import importlib
    cli_skill = importlib.import_module('powerspec.cli.skill')
    project, root = consumer(tmp_path)
    profile = root / 'profiles/scenarios.toml'
    profile.write_text(profile.read_text().replace('traits=[', 'traits=["@builtin/skill-bootstrap",'))
    dynamic(root / 'skills/a')
    entry = root / 'skills/a/SKILL.md'
    entry.write_text(entry.read_text().replace('name: branch-skill','name: a'))
    put(root / 'skills/a/languages/rust.md', 'INACTIVE-A')
    with open_workspace(project, agent='codex') as workspace:
        plans = plan_skills(workspace.bundle)
        assert [p.name for p in plans] == ['pspec-skill-bootstrap']
        result = provision_skills(plans, home=project/'home', registry=project/'registry')
        assert result.ok
    native = list((project / 'home').rglob('SKILL.md'))
    assert len(native) == 1 and native[0].parent.name == 'pspec-skill-bootstrap'
    calls = []
    original = cli_skill.resolve_catalog_skill
    def tracked(workspace, selector, **kwargs):
        calls.append(selector)
        return original(workspace, selector, **kwargs)
    monkeypatch.setattr(cli_skill, 'resolve_catalog_skill', tracked)
    monkeypatch.chdir(project)
    runner = CliRunner()
    def hook():
        result = runner.invoke(app, ['resolve','hook','afterCompaction','--agent','codex'])
        assert result.exit_code == 0, result.output
        context = json.loads(result.stdout)['hookSpecificOutput']['additionalContext']
        for hidden in ('PROCEDURE-', 'DISCOVERY-', 'INACTIVE-A', 'Run <command>'):
            assert hidden not in context
        return context
    startup = hook()
    assert 'When reviewing A, use pspec:@local/a.' in startup
    assert calls == []
    # The fixture now enters scenario A. Its owning rule supplies the selector;
    # there is no separate user-name input and no speculative B/C lookup.
    args = ['resolve','skill','--ref','@local/a','--agent','codex','--change','review','--json']
    pending = runner.invoke(app, args)
    payload = json.loads(pending.stdout)
    assert payload['status'] == 'pending' and payload['skill_ref'] == '@local/a'
    assert [q['key'] for q in payload['questions']] == ['mode']
    put(root / 'current.toml', '[_change.review]\nmode="python"\ncommand="ACTIVE-A"')
    result = runner.invoke(app, args)
    payload = json.loads(result.stdout)
    assert payload['status'] == 'resolved' and 'Run ACTIVE-A.' in payload['content']
    for hidden in ('PROCEDURE-b','PROCEDURE-c','INACTIVE-A','SUPPORT-a'):
        assert hidden not in payload['content']
    assert calls == ['@local/a', '@local/a']
    assert hook() == startup
    assert calls == ['@local/a', '@local/a']
    # A later B scenario retrieves ordinary B; C remains deferred.
    later = runner.invoke(app, ['resolve','skill','--ref','@local/b','--agent','codex','--json'])
    payload = json.loads(later.stdout)
    assert payload['status'] == 'resolved' and 'PROCEDURE-b' in payload['content']
    assert 'PROCEDURE-c' not in payload['content']
    assert calls == ['@local/a', '@local/a', '@local/b']
    # Repeat through a real exited process before reading its supporting file.
    exited = run(project, 'resolve','skill','--ref','@local/b','--agent','codex','--json')
    assert exited.returncode == 0, exited.stderr
    assert Path(json.loads(exited.stdout)['skill_path'], 'references/detail.md').read_text() == 'SUPPORT-b'
    assert list((project / 'home').rglob('SKILL.md')) == native

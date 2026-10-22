"""Real console boundary fixtures, with no access to the user's native assets."""
import json
import os
from pathlib import Path
import subprocess

import pytest

from test_skill_cli import console, put, snapshot

GLOBALS = ['builtin', 'adhd-friendly', 'zmem-lifecycle', 'repository-investigation', 'pspec-smarter-decision']


def consumer(tmp_path):
    project = tmp_path / 'project'
    (project / '.git').mkdir(parents=True)
    root = project / 'openspec/.pspec'
    put(root / 'config.toml', 'profile="@local/scenarios"\nexclude-profiles=' + json.dumps(['@builtin/'+n for n in GLOBALS]))
    put(root / 'profiles/scenarios.toml', 'skills=["@builtin/pspec-skill-bootstrap"]\n'
        'resolve-skills=["@local/a", "@local/b", "@local/c"]\n'
        'contexts=["@local/scenarios"]\ntraits=["@local/scenarios"]')
    put(root / 'guidance/scenarios.md', 'When reviewing A, use pspec:@local/a.\nWhen reviewing B, use pspec:@local/b.')
    put(root / 'contexts/scenarios.toml', '[[attach.context]]\nbody_file="guidance/scenarios.md"')
    put(root / 'traits/scenarios.toml', 'hooks=["sessionStart", "afterCompaction"]\nbody_file="guidance/scenarios.md"')
    for name in 'abc':
        put(root / f'skills/{name}/SKILL.md', f'---\nname: {name}\ndescription: DISCOVERY-{name}\n---\nPROCEDURE-{name}\nSee references/detail.md.\n')
        put(root / f'skills/{name}/references/detail.md', f'SUPPORT-{name}')
    return project, root


def run(project, *args, alias='pspec'):
    env = {**os.environ, 'HOME': str(project / 'home'), 'USERPROFILE': str(project / 'home'),
           'CODEX_HOME': str(project / 'home/.codex')}
    return subprocess.run([console(alias), *args], cwd=project, env=env, text=True, capture_output=True, timeout=30)


def test_status_console_and_documented_profile_plan(tmp_path):
    from powerspec.catalog import Catalog
    from powerspec.profiles import compose
    from powerspec.resources import builtin_catalog_root
    from powerspec.provisioning import plan_skills
    project, root = consumer(tmp_path)
    before = snapshot(project)
    with builtin_catalog_root() as builtin:
        bundle = compose(Catalog(builtin=builtin, sources={'local': root}), '@local/scenarios',
                         agent='codex', exclude_profiles=['@builtin/'+n for n in GLOBALS])
        assert [p.name for p in plan_skills(bundle)] == ['pspec-skill-bootstrap']
        assert {t.resource.name for t in bundle.resolve_skills} == set('abc')
    result = run(project, 'status', '--json')
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload['skills'] == ['@builtin/pspec-skill-bootstrap']
    assert payload['resolve_skills'] == ['@local/a', '@local/b', '@local/c']
    human = run(project, 'status')
    assert human.returncode == 0, human.stderr
    assert 'Skills selected for installation: @builtin/pspec-skill-bootstrap' in human.stdout
    assert 'Resolve-only declarations: @local/a, @local/b, @local/c' in human.stdout
    assert snapshot(project) == before


def test_shared_scenario_guidance_delivers_rules_without_procedures(tmp_path):
    project, root = consumer(tmp_path)
    put(project / 'openspec/config.yaml', 'schema: spec-driven\n')
    result = run(project, 'sync')
    assert result.returncode == 0, result.stderr
    from ruamel.yaml import YAML
    document = YAML(typ='safe').load((project / 'openspec/config.yaml').read_text())
    rule = (root / 'guidance/scenarios.md').read_text()
    assert rule in document['context']
    for event in ('sessionStart', 'afterCompaction'):
        result = run(project, 'resolve', 'hook', event, '--agent', 'codex')
        assert result.returncode == 0, result.stderr
        body = json.loads(result.stdout)['hookSpecificOutput']['additionalContext']
        assert body == rule


def test_ordinary_reference_aliases_metadata_and_durable_support(tmp_path):
    project, root = consumer(tmp_path)
    before = snapshot(project)
    args = ('resolve', 'skill', '--ref', 'a', '--agent', 'codex')
    result = run(project, *args, '--json')
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload['status'] == 'resolved'
    assert payload['skill_ref'] == '@local/a'
    assert Path(payload['skill_path']) == root / 'skills/a'
    assert Path(payload['skill_path'], 'references/detail.md').read_text() == 'SUPPORT-a'
    markdown = run(project, *args, alias='powerspec')
    assert markdown.stdout == payload['content']
    for hidden in ['DISCOVERY-', 'PROCEDURE-b', 'PROCEDURE-c', 'SUPPORT-']:
        assert hidden not in markdown.stdout
    native = run(project, 'resolve', 'skill', '--path', payload['skill_path'], '--agent', 'codex')
    assert native.returncode == 0 and native.stdout.strip() == 'null'
    assert snapshot(project) == before


@pytest.mark.parametrize('selectors', [(), ('--ref','a','--path','missing'), ('--ref','tools/*'), ('--ref','unknown'),
                                     ('--ref','@builtin/pspec-tdd'), ('--ref','@local/unselected')])
def test_bad_catalog_invocation_has_no_payload_or_writes(tmp_path, selectors):
    project, root = consumer(tmp_path)
    put(root / 'skills/unselected/SKILL.md', '---\nname: unselected\n---\nDo not return')
    before = snapshot(project)
    result = run(project, 'resolve', 'skill', *selectors, '--agent','codex')
    assert result.returncode != 0
    assert result.stdout == ''
    assert snapshot(project) == before


def test_dynamic_pending_retry_preserves_exact_ref_and_change(tmp_path):
    project, root = consumer(tmp_path)
    put(root / 'skills/a/SKILL.md', '---\nname: a\n---\nUse <answer>.\n')
    put(root / 'skills/a/pspec.toml', 'version=2\nentry="SKILL.md"\n[[input]]\nid="answer"\ntype="string"\n'
        '[input.parser]\ntype="prompt"\nprompt="Which answer?"')
    args = ('resolve','skill','--ref','a','--agent','codex','--change','review-a')
    before = snapshot(project)
    result = run(project, *args, '--json')
    assert result.returncode == 0, result.stderr
    pending = json.loads(result.stdout)
    assert pending['status'] == 'pending' and pending['skill_ref'] == '@local/a'
    assert [q['key'] for q in pending['questions']] == ['answer']
    assert 'content' not in pending
    markdown = run(project, *args)
    assert '--ref "@local/a" --agent codex --change review-a' in markdown.stdout
    assert snapshot(project) == before
    put(root / 'current.toml', '[_change.review-a]\nanswer="confirmed"')
    result = run(project, 'resolve','skill','--ref',pending['skill_ref'],'--agent','codex','--change','review-a','--json')
    assert result.returncode == 0, result.stderr
    resolved = json.loads(result.stdout)
    assert resolved['content'].endswith('Use confirmed.\n')
    native = run(project, 'resolve','skill','--path',pending['skill_path'],'--agent','codex','--change','review-a')
    assert resolved['content'].endswith(native.stdout)


@pytest.mark.parametrize('manifest', ['broken = [', 'version=2\nentry="../outside.md"'])
def test_invalid_catalog_manifest_is_not_ordinary_fallback(tmp_path, manifest):
    project, root = consumer(tmp_path)
    put(root / 'skills/a/pspec.toml', manifest)
    result = run(project, 'resolve','skill','--ref','a','--agent','codex')
    assert result.returncode != 0 and result.stdout == ''


def test_catalog_requires_agent_and_consumer(tmp_path):
    project, _ = consumer(tmp_path)
    assert run(project, 'resolve','skill','--ref','a').returncode != 0
    outside = tmp_path / 'outside'
    outside.mkdir()
    result = run(outside, 'resolve','skill','--ref','a','--agent','codex')
    assert result.returncode != 0 and result.stdout == ''
    assert 'owning' in result.stderr


def test_editable_builtin_paths_remain_readable_after_exit(tmp_path):
    project, root = consumer(tmp_path)
    profile = root / 'profiles/scenarios.toml'
    profile.write_text('resolve-skills=["@builtin/pspec-tdd","@builtin/openspec-explore"]\n'
                       '[vars]\nlanguage="python"\nbuild_tool="uv"\ntest_runner="pytest"\ntest_command="uv run pytest"')
    for ref in ('@builtin/pspec-tdd', '@builtin/openspec-explore'):
        result = run(project, 'resolve','skill','--ref',ref,'--agent','codex','--json')
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload['status'] == 'resolved'
        path = Path(payload['skill_path'])
        assert (path / 'SKILL.md').is_file()
        assert 'powerspec-catalog-' not in str(path)
        if ref.endswith('pspec-tdd'):
            assert (path / 'languages/python.md').is_file()


def test_selected_response_does_not_resolve_siblings_or_inactive_branches(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from powerspec.cli import app
    import powerspec.catalog_skills as feature
    from test_skill_resolution import skill as dynamic
    project, root = consumer(tmp_path)
    dynamic(root / 'skills/a')
    entry = root / 'skills/a/SKILL.md'
    entry.write_text(entry.read_text().replace('name: branch-skill', 'name: a'))
    put(root / 'skills/a/languages/rust.md', 'INACTIVE-A')
    put(root / 'skills/b/pspec.toml', 'version=2\nentry="SKILL.md"\n[[input]]\nid="unneeded"\ntype="string"\n[input.parser]\ntype="prompt"\nprompt="QUESTION-B"')
    put(root / 'current.toml', '[vars]\nmode="python"\ncommand="ACTIVE-A"')
    calls = []
    original = feature.resolve_skill
    def tracked(path, *args, **kwargs):
        calls.append(path)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(feature, 'resolve_skill', tracked)
    def forbidden(*a, **k):
        pytest.fail('read-only resolution crossed a lifecycle boundary')
    import zuat.pub
    from powerspec.sources import SaucepanSources
    for method in ('ensure','acquire'):
        monkeypatch.setattr(SaucepanSources, method, forbidden)
    for method in ('locate_skill','install','uninstall'):
        monkeypatch.setattr(zuat.pub, method, forbidden)
    monkeypatch.chdir(project)
    before = snapshot(project)
    result = CliRunner().invoke(app, ['resolve','skill','--ref','a','--agent','codex','--json'])
    assert result.exit_code == 0 and result.stderr == '', result.output
    payload = json.loads(result.stdout)
    assert payload['status'] == 'resolved' and 'Run ACTIVE-A.' in payload['content']
    assert calls == [root / 'skills/a']
    for hidden in ('INACTIVE-A','PROCEDURE-b','PROCEDURE-c','DISCOVERY-','QUESTION-B','SUPPORT-'):
        assert hidden not in payload['content']
    assert snapshot(project) == before

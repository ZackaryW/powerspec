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

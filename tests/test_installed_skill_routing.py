"""Run against an explicitly supplied isolated installed distribution."""
import json
import os
from pathlib import Path
import subprocess

import pytest

from test_catalog_skill_cli import consumer, GLOBALS
from test_skill_cli import put, snapshot


ENTRYPOINT = os.environ.get('POWERSPEC_TEST_ENTRYPOINT')
pytestmark = pytest.mark.skipif(not ENTRYPOINT, reason='set POWERSPEC_TEST_ENTRYPOINT to an isolated wheel entrypoint')


def test_wheel_catalog_native_routes_and_post_exit_support(tmp_path):
    project, root = consumer(tmp_path)
    put(root / 'config.toml', 'profile="@local/scenarios"\nexclude-profiles=' + json.dumps(
        ['@builtin/'+n for n in GLOBALS if n != 'builtin']))
    put(root / 'profiles/scenarios.toml', 'resolve-skills=["@builtin/pspec-tdd","@builtin/openspec-explore"]\n'
        '[vars]\nlanguage="python"\nbuild_tool="uv"\ntest_runner="pytest"\ntest_command="uv run pytest"')
    env = {**os.environ, 'HOME': str(project/'home'), 'USERPROFILE': str(project/'home'),
           'CODEX_HOME': str(project/'home/.codex')}
    env.pop('PYTHONPATH', None)
    before = snapshot(project)
    def invoke(*args, alias=False):
        executable = Path(ENTRYPOINT)
        if alias:
            executable = executable.with_name('powerspec' + executable.suffix)
        result = subprocess.run([str(executable), *args], cwd=project, env=env,
                                capture_output=True, text=True, timeout=30)
        assert result.returncode == 0 and result.stderr == '', (result.stdout, result.stderr)
        return result.stdout
    status = json.loads(invoke('status','--json'))
    assert '@builtin/skill-bootstrap' in status['traits']
    for ref in ('@builtin/pspec-tdd', '@builtin/openspec-explore'):
        args = ('resolve','skill','--ref',ref,'--agent','codex')
        result = json.loads(invoke(*args, '--json'))
        assert result['content'] == invoke(*args, alias=True)
        path = Path(result['skill_path'])
        assert path.is_relative_to(Path(ENTRYPOINT).parent.parent)
        assert 'site-packages' in path.parts
        assert (path/'SKILL.md').is_file()
        native = invoke('resolve','skill','--path',str(path),'--agent','codex')
        if ref.endswith('pspec-tdd'):
            assert result['content'].endswith(native)
            assert (path/'languages/python.md').read_text(encoding='utf-8')
        else:
            assert native.strip() == 'null'
    hook = json.loads(invoke('resolve','hook','afterCompaction','--agent','codex'))
    assert 'pspec-skill-bootstrap' in hook['hookSpecificOutput']['additionalContext']
    assert snapshot(project) == before

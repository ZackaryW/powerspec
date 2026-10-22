"""Opt-in installed entrypoint acceptance using published artifacts and isolated homes.

Set POWERSPEC_TEST_ENTRYPOINT to an independently installed pspec executable and
SAUCEPAN_RELEASE_ASSETS to verified v0.11.0 assets. No provider checkout is used.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from uuid import uuid4

import pytest

ENTRYPOINT = os.environ.get('POWERSPEC_TEST_ENTRYPOINT')
ASSETS = os.environ.get('SAUCEPAN_RELEASE_ASSETS')
EVIDENCE = os.environ.get('POWERSPEC_ACCEPTANCE_EVIDENCE')
pytestmark = pytest.mark.skipif(os.name != 'nt' or not ENTRYPOINT or not ASSETS,
    reason='Windows acceptance requires independent wheel installation and released artifacts')


def call(argv, *, cwd, env, code=0):
    result = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=600)
    if result.returncode != code:
        pytest.fail(f'{argv}: exit {result.returncode}\n{result.stdout}\n{result.stderr}')
    return result


@pytest.mark.parametrize('migrate', [False, True])
def test_installed_entrypoint_released_setup_reuse_upgrade(migrate):
    with tempfile.TemporaryDirectory(prefix='ps-wheel-') as temporary:
        root = Path(temporary)
        home, project, remote = root / 'home', root / 'project', root / 'remote'
        for directory in (home, project, remote):
            directory.mkdir()
        env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), CODEX_HOME=str(home / '.codex'),
                   ZUAT_HOME=str(root / 'registry'), LOCALAPPDATA=str(home / 'AppData/Local'),
                   APPDATA=str(home / 'AppData/Roaming'))
        for name in ('POWERSPEC_SAUCEPAN', 'SAUCEPAN_ROOT', 'POWERSPEC_SAUCEPAN_CREDENTIAL_FILE', 'PYTHONPATH'):
            env.pop(name, None)
        env['PATH'] = os.pathsep.join(p for p in env['PATH'].split(os.pathsep)
                                    if '.cargo' not in p.lower() and 'saucepan' not in p.lower())
        for directory in (project, remote):
            call(['git', 'init', '-q', '-b', 'main'], cwd=directory, env=env)
        skill = remote / 'skills/example/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('---\nname: example\ndescription: Fixture skill.\n---\n\nFirst generation\n')
        call(['git', 'add', '.'], cwd=remote, env=env)
        commit = ['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm']
        call([*commit, 'first'], cwd=remote, env=env)
        consumer = project / 'openspec/.pspec'
        (consumer / 'profiles').mkdir(parents=True)
        config = consumer / 'config.toml'
        excluded = ['builtin', 'zmem-lifecycle', 'repository-investigation', 'adhd-friendly', 'pspec-smarter-decision']
        config.write_text('profile="@local/acceptance"\nexclude-profiles=' + json.dumps(['@builtin/' + n for n in excluded]) + '\n[vars]\n')
        (consumer / 'profiles/acceptance.toml').write_text('scope="user"\nskills=["fixture/skills/*"]\n'
            '[[source]]\nid="fixture"\nprovider="git"\norigin=' + json.dumps(str(remote)) + '\nreference="main"\n')
        (project / 'openspec/config.yaml').write_text('schema: spec-driven\n')
        target = home / '.saucepan/bin/saucepan.exe'
        migration = None
        if migrate:
            staged = root / 'provider'
            staged.mkdir()
            for name in ('saucepan.exe', 'install.ps1'):
                shutil.copyfile(Path(ASSETS) / name, staged / name)
            call([staged / 'saucepan.exe', '--root', target.parent.parent, 'init'], cwd=project, env=env)
            shutil.copyfile(staged / 'saucepan.exe', target)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            migration = json.loads(call(['powershell.exe', '-NoProfile', '-File', staged / 'install.ps1',
                '-Version', 'v0.11.0', '-Root', target.parent.parent, '-Operation', str(uuid4()),
                '-MigrateUnmanaged', '-ExpectedSha256', digest], cwd=project, env=env).stdout)
            assert migration['status'] == 'complete'
            assert hashlib.sha256(Path(migration['backup_paths'][0]).read_bytes()).hexdigest() == digest
        first = call([ENTRYPOINT, 'init', '--agent', 'codex'], cwd=project, env=env)
        assert 'Initialization complete' in first.stdout
        status = json.loads(call([target, '--root', target.parent.parent, 'setup-status'], cwd=project, env=env).stdout)
        assert status['state'] == 'ready' and status['installed_version'] == 'v0.11.0'
        before = hashlib.sha256(target.read_bytes()).hexdigest()
        selected_before = json.loads((consumer / 'saucepan-state.json').read_text())
        second = call([ENTRYPOINT, 'init', '--agent', 'codex'], cwd=project, env=env)
        assert 'reused' in second.stdout and 'Saucepan setup:' not in second.stderr
        doctor = json.loads(call([ENTRYPOINT, 'doctor', '--json'], cwd=project, env=env).stdout)
        assert next(c for c in doctor['checks'] if c['name']=='saucepan-installation')['status']=='ok'
        skill.write_text(skill.read_text().replace('First', 'Second'))
        call([*commit, 'second', '-a'], cwd=remote, env=env)
        upgraded = call([ENTRYPOINT, 'upgrade', '--agent', 'codex'], cwd=project, env=env)
        assert 'Upgrade complete' in upgraded.stdout and 'Saucepan setup:' not in upgraded.stderr
        assert 'Second generation' in (home / '.codex/skills/example/SKILL.md').read_text()
        assert hashlib.sha256(target.read_bytes()).hexdigest() == before
        selected_after = json.loads((consumer / 'saucepan-state.json').read_text())
        assert selected_after['selected'] != selected_before['selected']
        if EVIDENCE:
            path = Path(EVIDENCE)
            records = json.loads(path.read_text()) if path.exists() else []
            records.append(dict(migrated=migrate, entrypoint=ENTRYPOINT, status=status, migration=migration,
                launcher_sha256=before, init_stdout=first.stdout, init_stderr=first.stderr,
                selected_before=selected_before, selected_after=selected_after, doctor=doctor))
            path.write_text(json.dumps(records, indent=2))

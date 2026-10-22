"""Exercise commit eligibility through actual console commands and Git indexes."""

import json
import os
from pathlib import Path
import shlex
import subprocess
import sysconfig

import pytest


def git(root, *args, input=None, env=None):
    result = subprocess.run(['git', *args], cwd=root, env=env, input=input,
                            capture_output=True, timeout=15, check=True)
    return result.stdout


def put(root, name, content='content\n'):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    return path


@pytest.fixture
def repo(tmp_path, monkeypatch):
    for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR'):
        monkeypatch.delenv(key, raising=False)
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'user.name', 'Commit test')
    git(tmp_path, 'config', 'user.email', 'test@example.invalid')
    git(tmp_path, 'config', 'commit.gpgsign', 'false')
    return tmp_path


def check(root, *, alias='pspec', json_output=True, env=None):
    executable = Path(sysconfig.get_path('scripts')) / (alias + ('.exe' if os.name == 'nt' else ''))
    return subprocess.run([str(executable), 'check', 'commit', *(['--json'] if json_output else [])],
                          cwd=root, env=env, capture_output=True, text=True,
                          encoding='utf-8', timeout=15)


def snapshot(root):
    return {str(path.relative_to(root)): path.read_bytes()
            for path in root.rglob('*') if path.is_file()}


@pytest.mark.parametrize('alias', ['pspec', 'powerspec'])
def test_force_added_active_file_fails_and_preserves_all_state(repo, alias):
    active = 'openspec/changes/in-flight/proposal.md'
    put(repo, '.gitignore', 'openspec/changes/*\n!openspec/changes/archive/\n')
    put(repo, active)
    put(repo, 'src/application.py', 'value = 42\n')
    git(repo, 'add', '.gitignore', 'src/application.py')
    git(repo, 'add', '-f', active)
    before = snapshot(repo)
    result = check(repo, alias=alias)
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data == dict(ok=False, repository=str(repo.resolve()),
                        forbidden_paths=[active], unmerged_paths=[], errors=[])
    assert result.stderr == ''
    assert snapshot(repo) == before


def test_already_tracked_active_file_blocks_an_unrelated_checkpoint(repo):
    active = 'openspec/changes/old/tasks.md'
    put(repo, active)
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'old tracked planning')
    put(repo, 'code.py', 'answer = 42\n')
    git(repo, 'add', 'code.py')
    assert git(repo, 'diff', '--cached', '--name-only').decode().splitlines() == ['code.py']
    result = check(repo)
    assert result.returncode == 1
    assert json.loads(result.stdout)['forbidden_paths'] == [active]
    human = check(repo, json_output=False)
    assert human.returncode == 1 and human.stdout == ''
    assert active in human.stderr


def test_local_planning_and_code_checkpoint_then_archive_commit(repo):
    active = 'openspec/changes/feature/proposal.md'
    put(repo, active, 'accepted plan\n')
    put(repo, 'code.py')
    git(repo, 'add', 'code.py')
    assert check(repo).returncode == 0
    git(repo, 'commit', '-qm', 'verified code checkpoint')
    assert git(repo, 'ls-tree', '-r', '--name-only', 'HEAD').decode().splitlines() == ['code.py']
    archive = 'openspec/changes/archive/2026-10-22-feature/proposal.md'
    (repo / archive).parent.mkdir(parents=True)
    (repo / active).rename(repo / archive)
    put(repo, 'openspec/specs/feature/spec.md', 'synced requirement\n')
    git(repo, 'add', archive, 'openspec/specs/feature/spec.md')
    assert check(repo).returncode == 0
    git(repo, 'commit', '-qm', 'archive artifacts')
    tree = git(repo, 'ls-tree', '-r', '--name-only', 'HEAD').decode().splitlines()
    assert active not in tree and archive in tree


def test_untracking_preserves_local_active_file_and_allows_archive(repo):
    active = 'openspec/changes/old/proposal.md'
    archive = 'openspec/changes/archive/completed/proposal.md'
    put(repo, active)
    git(repo, 'add', active)
    git(repo, 'commit', '-qm', 'legacy')
    before = (repo / active).read_bytes()
    git(repo, 'rm', '--cached', '--', active)
    put(repo, archive)
    git(repo, 'add', archive)
    result = check(repo)
    assert result.returncode == 0
    assert (repo / active).read_bytes() == before
    assert json.loads(result.stdout)['forbidden_paths'] == []


def test_boundaries_nested_consumers_and_case_variants(repo):
    rejected = ['packages/one/openspec/changes/current/tasks.md',
                'packages/two/OpenSpec/Changes/draft/proposal.md',
                'openspec/changes/archive-draft/plan.md',
                'packages/three/openspec/changes/Archive/plan.md',
                'openspec/changes/local/café plan.md']
    allowed = ['openspec/changes/archive/done/tasks.md', 'openspec/specs/policy/spec.md',
               'docs/openspec-notes/changes/notes.md']
    for path in rejected + allowed:
        put(repo, path)
    git(repo, 'add', '.')
    result = check(repo / 'packages/one')
    assert result.returncode == 1
    assert set(json.loads(result.stdout)['forbidden_paths']) == set(rejected)


def test_intent_to_add_active_path_is_rejected(repo):
    active = 'openspec/changes/planned/tasks.md'
    put(repo, active)
    git(repo, 'add', '-N', active)
    result = check(repo)
    assert result.returncode == 1
    assert json.loads(result.stdout)['forbidden_paths'] == [active]


def test_alternative_index_controls_check(repo):
    active = 'openspec/changes/active/tasks.md'
    put(repo, 'safe.py')
    git(repo, 'add', 'safe.py')
    selected = repo / '.git/selected.index'
    env = dict(os.environ, GIT_INDEX_FILE=str(selected))
    put(repo, active)
    git(repo, 'add', active, env=env)
    assert check(repo).returncode == 0
    before = selected.read_bytes()
    result = check(repo, env=env)
    assert result.returncode == 1
    assert json.loads(result.stdout)['forbidden_paths'] == [active]
    assert selected.read_bytes() == before


def test_conflict_and_corrupt_index_cannot_pass(repo):
    blob = git(repo, 'hash-object', '-w', '--stdin', input=b'base\n').strip()
    git(repo, 'update-index', '-z', '--index-info',
        input=b'100644 ' + blob + b' 1\tcode.py\0')
    result = check(repo)
    assert result.returncode == 1
    assert json.loads(result.stdout)['unmerged_paths'] == ['code.py']
    (repo / '.git/index').write_bytes(b'corrupt index')
    before = snapshot(repo)
    result = check(repo)
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data['ok'] is False and data['errors']
    assert snapshot(repo) == before


def test_outside_repository_and_missing_git_are_failures(tmp_path_factory, repo):
    outside = tmp_path_factory.mktemp('outside-git')
    result = check(outside)
    assert result.returncode == 1
    assert json.loads(result.stdout)['errors']
    env = dict(os.environ, PATH='')
    result = check(repo, env=env)
    assert result.returncode == 1
    assert json.loads(result.stdout)['errors']


def test_sparse_index_cannot_hide_active_files(repo):
    active = 'openspec/changes/active/proposal.md'
    put(repo, active)
    put(repo, 'src/code.py')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'legacy')
    git(repo, 'sparse-checkout', 'set', '--cone', '--sparse-index', 'src')
    assert not (repo / active).exists()
    before = (repo / '.git/index').read_bytes()
    result = check(repo)
    assert result.returncode == 1
    assert json.loads(result.stdout)['forbidden_paths'] == [active]
    assert (repo / '.git/index').read_bytes() == before


def test_linked_worktree_check_is_independent(repo):
    put(repo, 'base.py')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'base')
    linked = repo / 'linked'
    git(repo, 'worktree', 'add', '-qb', 'linked', str(linked))
    active = 'openspec/changes/linked/tasks.md'
    put(linked, active)
    git(linked, 'add', active)
    assert check(repo).returncode == 0
    result = check(linked)
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data['repository'] == str(linked.resolve())
    assert data['forbidden_paths'] == [active]


def test_index_paths_do_not_follow_symlinks_or_split_on_tabs(repo):
    blob = git(repo, 'hash-object', '-w', '--stdin', input=b'elsewhere').strip()
    forbidden = ['one/openspec/changes', 'two/openspec/changes/archive',
                 'three/openspec/changes/active/odd\tname\n.md']
    allowed = 'four/openspec/changes/archive/done/link'
    records = b''.join(b'120000 ' + blob + b'\t' + path.encode() + b'\0'
                       for path in forbidden + [allowed])
    git(repo, '-c', 'core.protectNTFS=false', 'update-index', '-z', '--index-info', input=records)
    result = check(repo)
    assert result.returncode == 1
    assert set(json.loads(result.stdout)['forbidden_paths']) == set(forbidden)


def test_explicit_precommit_hook_rejects_commit_without_changing_head(repo):
    # Install only in this disposable test repo, proving command exit behavior
    # can gate Git. The product itself never installs or overwrites hooks.
    put(repo, 'base.py')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'base')
    head = git(repo, 'rev-parse', 'HEAD')
    executable = Path(sysconfig.get_path('scripts')) / ('pspec.exe' if os.name == 'nt' else 'pspec')
    hook = put(repo, '.git/hooks/pre-commit',
               '#!/bin/sh\nexec ' + shlex.quote(executable.as_posix()) + ' check commit\n')
    hook.write_bytes(hook.read_bytes().replace(b'\r\n', b'\n'))
    hook.chmod(0o755)
    put(repo, 'openspec/changes/active/tasks.md')
    git(repo, 'add', 'openspec/changes/active/tasks.md')
    result = subprocess.run(['git', 'commit', '-m', 'should be rejected'], cwd=repo,
                            capture_output=True, timeout=15)
    assert result.returncode != 0
    assert git(repo, 'rev-parse', 'HEAD') == head
    # Git itself can refresh index stat data before hooks; the staged content
    # contract, unlike exact index bytes, applies across a git commit attempt.
    assert git(repo, 'diff', '--cached', '--name-only').decode().splitlines() == [
        'openspec/changes/active/tasks.md']


def test_repository_ignore_rules_keep_active_local_and_archives_addable(repo):
    authored = Path(__file__).resolve().parents[1] / '.gitignore'
    put(repo, '.gitignore', authored.read_text())
    active = 'openspec/changes/feature/tasks.md'
    nested = 'packages/app/openspec/changes/feature/tasks.md'
    archived = 'openspec/changes/archive/done/tasks.md'
    nested_archive = 'packages/app/openspec/changes/archive/done/tasks.md'
    for path in (active, nested, archived, nested_archive, 'code.py'):
        put(repo, path)
    git(repo, 'add', '.')
    indexed = set(git(repo, 'ls-files', '-z').decode().rstrip('\0').split('\0'))
    assert indexed == {'.gitignore', 'code.py', archived, nested_archive}
    assert (repo / active).is_file() and (repo / nested).is_file()
    assert check(repo).returncode == 0
    git(repo, 'add', '-f', active)
    assert check(repo).returncode == 1

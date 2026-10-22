"""Native index observations, independent of OpenSpec path conventions."""

import subprocess

import pytest

from powerspec.utils.git_index import IndexReadError, read_index


def git(root, *args, input=None):
    return subprocess.run(['git', *args], cwd=root, input=input,
                          capture_output=True, check=True, timeout=15).stdout


@pytest.fixture
def repo(tmp_path, monkeypatch):
    for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR'):
        monkeypatch.delenv(key, raising=False)
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'user.email', 'test@example.invalid')
    git(tmp_path, 'config', 'user.name', 'Index test')
    git(tmp_path, 'config', 'commit.gpgsign', 'false')
    git(tmp_path, 'config', 'core.autocrlf', 'false')
    return tmp_path


def put(root, name, content='content\n'):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    return path


def test_unborn_and_nested_whole_index_are_read_only(repo):
    assert read_index(repo).entries == ()
    put(repo, 'top.txt')
    put(repo, 'nested/café file.txt', 'unicode\n')
    git(repo, 'add', '.')
    before = (repo / '.git/index').read_bytes()
    result = read_index(repo / 'nested')
    assert result.root == repo.resolve()
    assert {item.path for item in result.entries} == {'top.txt', 'nested/café file.txt'}
    assert {item.mode for item in result.entries} == {'100644'}
    assert {item.stage for item in result.entries} == {0}
    for item in result.entries:
        assert git(repo, 'cat-file', 'blob', item.object_id) == (repo / item.path).read_bytes()
    assert (repo / '.git/index').read_bytes() == before


def test_alternative_index_keeps_relative_environment(repo, monkeypatch):
    put(repo, 'ordinary.txt')
    git(repo, 'add', 'ordinary.txt')
    original = (repo / '.git/index').read_bytes()
    nested = repo / 'nested'
    nested.mkdir()
    monkeypatch.setenv('GIT_INDEX_FILE', '.git/selected.index')
    put(repo, 'selected.txt')
    git(nested, 'add', '../selected.txt')
    selected = (repo / '.git/selected.index').read_bytes()
    result = read_index(nested)
    assert [item.path for item in result.entries] == ['selected.txt']
    assert (repo / '.git/index').read_bytes() == original
    assert (repo / '.git/selected.index').read_bytes() == selected


def test_conflict_stages_are_preserved(repo):
    blob = git(repo, 'hash-object', '-w', '--stdin', input=b'conflict\n').strip()
    records = b''.join(b'100644 ' + blob + b' ' + str(stage).encode() + b'\tconflict.txt\0'
                       for stage in (1, 2, 3))
    git(repo, 'update-index', '-z', '--index-info', input=records)
    result = read_index(repo)
    assert [(item.path, item.stage) for item in result.entries] == [
        ('conflict.txt', 1), ('conflict.txt', 2), ('conflict.txt', 3)]


def test_linked_worktree_uses_its_own_index(repo, tmp_path):
    put(repo, 'base.txt')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'base')
    linked = tmp_path / 'linked'
    git(repo, 'worktree', 'add', '-qb', 'linked', str(linked))
    put(linked, 'only-linked.txt')
    git(linked, 'add', 'only-linked.txt')
    assert read_index(linked).root == linked.resolve()
    assert {item.path for item in read_index(linked).entries} == {'base.txt', 'only-linked.txt'}
    assert {item.path for item in read_index(repo).entries} == {'base.txt'}


def test_nul_records_preserve_tabs_and_newlines(repo):
    # Index entries need no working file; Windows forbids these filename characters.
    blob = git(repo, 'hash-object', '-w', '--stdin', input=b'odd\n').strip()
    name = 'odd\tname\n.txt'
    git(repo, '-c', 'core.protectNTFS=false', 'update-index', '-z', '--index-info',
        input=b'100644 ' + blob + b'\t' + name.encode() + b'\0')
    assert [item.path for item in read_index(repo).entries] == [name]


def test_invalid_repository_and_corrupt_index_fail(repo, tmp_path_factory):
    with pytest.raises(IndexReadError):
        read_index(tmp_path_factory.mktemp('outside'))
    with pytest.raises(IndexReadError):
        read_index(repo / 'does-not-exist')
    (repo / '.git/index').write_bytes(b'corrupt')
    with pytest.raises(IndexReadError):
        read_index(repo)


def test_missing_git_is_a_located_error(repo, monkeypatch):
    monkeypatch.setenv('PATH', '')
    with pytest.raises(IndexReadError):
        read_index(repo)

"""Default provisioning must not poison the store it is about to initialize."""
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from powerspec import saucepan_tool as tool
from powerspec.catalog import ConfigurationError

REAL_MANAGER_FACTORY = tool._managed_saucepan

@pytest.fixture
def installation(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: tmp_path))
    monkeypatch.delenv('POWERSPEC_SAUCEPAN', raising=False)
    target = tool.saucepan_executable_path()
    events = []

    class Manager:
        def __init__(self, destination):
            self.destination = destination

        def ensure(self, **kwargs):
            events.append(('ensure', self.destination))
            self.destination.write_bytes(b'manager')
            return SimpleNamespace(destination=self.destination)

    class Client:
        def __init__(self, *, executable, root):
            self.root = Path(root)
            self.executable = Path(executable)

        def init(self):
            events.append(('init', self.executable))
            assert not self.executable.is_relative_to(self.root)
            assert not self.root.exists() or not list(self.root.iterdir())
            self.root.mkdir(exist_ok=True)
            (self.root / 'root.json').write_text('{}')

    monkeypatch.setattr(tool, '_managed_saucepan', Manager)
    monkeypatch.setattr(tool, '_probe', lambda path: '0.10.0')
    monkeypatch.setattr(tool, '_validate', lambda *args: None)
    monkeypatch.setattr('saucepan_sdk.Client', Client)
    return SimpleNamespace(home=tmp_path, target=target, root=target.parent.parent, events=events)


def test_default_initializes_before_publication_and_reuses_store(installation):
    data = installation
    assert tool.ensure_saucepan_binary() == data.target
    assert (data.root / 'root.json').is_file()
    assert data.target.read_bytes() == b'manager'
    assert [event[0] for event in data.events] == ['ensure', 'init']
    tool.ensure_saucepan_binary()
    assert [event[0] for event in data.events].count('init') == 1


def test_binary_only_recovery_preserves_originals(installation):
    data = installation
    data.target.parent.mkdir(parents=True)
    data.target.write_bytes(b'original')
    data.target.with_name('saucepan-check.json').write_text('invalid but preserved')
    tool.ensure_saucepan_binary()
    backups = list(data.home.glob('.powerspec-saucepan-backup-*'))
    assert len(backups) == 1
    assert (backups[0] / data.target.name).read_bytes() == b'original'
    assert (backups[0] / 'saucepan-check.json').read_text() == 'invalid but preserved'


@pytest.mark.parametrize('location', ['root', 'bin'])
def test_unknown_content_is_never_relocated(installation, location):
    data = installation
    directory = data.root if location == 'root' else data.target.parent
    directory.mkdir(parents=True)
    unknown = directory / 'keep.txt'
    unknown.write_text('mine')
    with pytest.raises(ConfigurationError, match='unrecognized'):
        tool.ensure_saucepan_binary()
    assert unknown.read_text() == 'mine'
    assert not data.events


def test_init_failure_preserves_backup_and_retry(installation, monkeypatch):
    data = installation
    data.target.parent.mkdir(parents=True)
    data.target.write_bytes(b'original')
    from saucepan_sdk import Client
    normal = Client.init
    monkeypatch.setattr(Client, 'init', lambda self: (_ for _ in ()).throw(ValueError('init refused')))
    with pytest.raises(ConfigurationError, match='preserved.*powerspec-saucepan-backup'):
        tool.ensure_saucepan_binary()
    assert not data.target.exists()
    assert len(list(data.home.glob('.powerspec-saucepan-backup-*'))) == 1
    monkeypatch.setattr(Client, 'init', normal)
    assert tool.ensure_saucepan_binary() == data.target


def test_occupied_lock_does_not_touch_root(installation):
    data = installation
    lock = data.home / '.powerspec-saucepan-bootstrap.lock'
    lock.write_text('another process')
    with pytest.raises(ConfigurationError, match='already in progress'):
        tool.ensure_saucepan_binary()
    assert not data.root.exists()
    assert lock.read_text() == 'another process'


def test_linked_bin_is_not_recovered(installation):
    data = installation
    external = data.home / 'elsewhere'
    external.mkdir()
    data.root.mkdir()
    try:
        data.target.parent.symlink_to(external, target_is_directory=True)
    except OSError:
        pytest.skip('symlink creation unavailable')
    with pytest.raises(ConfigurationError, match='linked'):
        tool.ensure_saucepan_binary()
    assert not list(external.iterdir())


def test_invalid_recovery_binary_is_preserved(installation, monkeypatch):
    data = installation
    data.target.parent.mkdir(parents=True)
    data.target.write_bytes(b'old')
    monkeypatch.setattr(tool, '_probe', lambda path: '0.1.0')
    with pytest.raises(ConfigurationError, match='unsupported'):
        tool.ensure_saucepan_binary()
    assert data.target.read_bytes() == b'old'
    assert not data.events


def test_publication_failure_keeps_initialized_store_and_backup(installation, monkeypatch):
    from powerspec import saucepan_bootstrap as bootstrap
    data = installation
    data.target.parent.mkdir(parents=True)
    data.target.write_bytes(b'original')
    normal = bootstrap.os.replace
    monkeypatch.setattr(bootstrap.os, 'replace', lambda *args: (_ for _ in ()).throw(OSError('disk error')))
    with pytest.raises(ConfigurationError, match='preserved at'):
        tool.ensure_saucepan_binary()
    assert (data.root / 'root.json').is_file()
    assert not data.target.exists()
    assert len(list(data.home.glob('.powerspec-saucepan-backup-*'))) == 1
    monkeypatch.setattr(bootstrap.os, 'replace', normal)
    tool.ensure_saucepan_binary()
    assert [event[0] for event in data.events].count('init') == 1


def test_interrupted_initialization_is_delegated(installation, monkeypatch):
    from saucepan_sdk import Client
    data = installation
    marker = data.root / '.staging/initializing.json'
    marker.parent.mkdir(parents=True)
    marker.write_text('owned by Saucepan')
    def resume(self):
        assert marker.read_text() == 'owned by Saucepan'
        (self.root / 'root.json').write_text('{}')
    monkeypatch.setattr(Client, 'init', resume)
    assert tool.ensure_saucepan_binary() == data.target


def test_new_unknown_file_during_staging_prevents_relocation(installation, monkeypatch):
    data = installation
    data.target.parent.mkdir(parents=True)
    data.target.write_bytes(b'original')
    original = tool._managed_saucepan
    def manager(path):
        result = original(path)
        ensure = result.ensure
        def changed(**kwargs):
            (data.root / 'foreign').write_text('keep')
            return ensure(**kwargs)
        result.ensure = changed
        return result
    monkeypatch.setattr(tool, '_managed_saucepan', manager)
    with pytest.raises(ConfigurationError, match='unrecognized'):
        tool.ensure_saucepan_binary()
    assert data.target.read_bytes() == b'original'
    assert not list(data.home.glob('.powerspec-saucepan-backup-*'))


@pytest.mark.parametrize('recovery', [False, True])
def test_real_zuu_check_cache_survives_stage_and_final_identity(installation, monkeypatch, recovery):
    from zuu.case16 import GitHubReleaseResolver
    from zuu.case17 import FileCheckStateStore
    data = installation
    discovery = []
    monkeypatch.setattr(tool, '_managed_saucepan', REAL_MANAGER_FACTORY)
    monkeypatch.setattr(GitHubReleaseResolver, 'resolve_version', lambda self: discovery.append(1) or '0.10.0')
    monkeypatch.setattr(GitHubReleaseResolver, 'resolve', lambda self, version, destination, **kwargs: destination.write_bytes(b'manager'))
    if recovery:
        data.target.parent.mkdir(parents=True)
        REAL_MANAGER_FACTORY(data.target).ensure()
        assert discovery == [1]
    tool.ensure_saucepan_binary()
    state = FileCheckStateStore(data.target.with_name('saucepan-check.json')).load()
    assert state.destination == os.path.normcase(os.path.abspath(data.target))
    assert state.installed_version == '0.10.0'
    tool.ensure_saucepan_binary()
    assert discovery == [1]


@pytest.mark.parametrize('name', ['root', 'binary', 'record'])
def test_linked_recovery_paths_are_preserved(installation, name):
    data = installation
    external = data.home / 'external'
    external.mkdir()
    if name == 'root':
        link, value = data.root, external
    else:
        data.target.parent.mkdir(parents=True)
        value = external / 'value'
        value.write_text('untouched')
        link = data.target if name == 'binary' else data.target.with_name('saucepan-check.json')
    try:
        link.symlink_to(value, target_is_directory=name == 'root')
    except OSError:
        pytest.skip('symlink creation unavailable')
    with pytest.raises(ConfigurationError, match='linked'):
        tool.ensure_saucepan_binary()
    assert link.is_symlink()
    assert not data.events


def test_unwritable_check_cache_does_not_lose_working_binary(installation, monkeypatch):
    from zuu.case16 import GitHubReleaseResolver
    from zuu.case17 import FileCheckStateStore
    data = installation
    monkeypatch.setattr(tool, '_managed_saucepan', REAL_MANAGER_FACTORY)
    monkeypatch.setattr(GitHubReleaseResolver, 'resolve_version', lambda self: '0.10.0')
    monkeypatch.setattr(GitHubReleaseResolver, 'resolve', lambda self, version, destination, **kwargs: destination.write_bytes(b'manager'))
    monkeypatch.setattr(FileCheckStateStore, 'save', lambda *args: (_ for _ in ()).throw(OSError('read only')))
    assert tool.ensure_saucepan_binary().read_bytes() == b'manager'
    assert (data.root / 'root.json').is_file()

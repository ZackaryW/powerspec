"""Powerspec's pinned, verified, self-managed milkpan."""
import hashlib
import io
import tarfile
import zipfile

import pytest

from powerspec.catalog import ConfigurationError, MetadataUnavailable
from powerspec.milkpan_binary import (MILKPAN, MANAGER_SCOPE, TARGETS, Release, default_home, download,
                                      ensure_consumer_policy,
                                      ensure_milkpan, extract, inspect_milkpan, link_executable, manager_state)

from milkpan_release_fixture import release_server


@pytest.fixture(autouse=True)
def no_override(monkeypatch):
    monkeypatch.delenv('POWERSPEC_MILKPAN', raising=False)


def test_every_supported_platform_is_pinned():
    for target in TARGETS.values():
        name, digest = MILKPAN.asset(target)
        assert name.startswith(f'milkpan-{MILKPAN.tag}-') and len(digest) == 64


def test_unsupported_platforms_name_the_supported_ones():
    with pytest.raises(ConfigurationError, match='supported: Windows/x86_64'):
        MILKPAN.target('Plan9', 'mips')
    assert MILKPAN.target('Linux', 'amd64') == 'x86_64-unknown-linux-gnu'


def test_unsafe_archive_members_are_rejected(tmp_path):
    archive = tmp_path / 'evil.zip'
    with zipfile.ZipFile(archive, 'w') as bundle:
        bundle.writestr('../escape/milkpan.exe', 'x')
    with pytest.raises(ConfigurationError, match='unsafe'):
        extract(archive, tmp_path / 'out')
    tarball = tmp_path / 'evil.tar.gz'
    with tarfile.open(tarball, 'w:gz') as bundle:
        info = tarfile.TarInfo('link')
        info.type = tarfile.SYMTYPE
        info.linkname = '/etc/passwd'
        bundle.addfile(info)
    with pytest.raises(ConfigurationError):
        extract(tarball, tmp_path / 'out2')


def test_downloads_must_match_the_pin(tmp_path):
    with release_server(['v0.2.0'], MILKPAN.target()) as (release, _):
        pinned = release('v0.2.0')
        name, digest = pinned.asset(pinned.target())
        url = f'{pinned.download_base}/v0.2.0/{name}'
        with pytest.raises(ConfigurationError, match='checksum mismatch'):
            download(url, tmp_path / name, '0' * 64)
        assert not (tmp_path / name).exists()
        download(url, tmp_path / name, digest)
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == digest


def test_bootstrap_links_and_later_runs_reuse_without_download(tmp_path):
    home = tmp_path / 'home'
    with release_server(['v0.2.0'], MILKPAN.target()) as (release, requests):
        pinned = release('v0.2.0')
        with pytest.raises(MetadataUnavailable):
            inspect_milkpan(home, release=pinned)
        assert requests == [], 'inspect never downloads'
        client = ensure_milkpan(home, release=pinned)
        assert client.executable == str(link_executable(home))
        assert manager_state(client, pinned, pinned.target()) == 'current'
        before = len(requests)
        ensure_milkpan(home, release=pinned)
        assert len(requests) == before, 'a current link needs no network'
        assert inspect_milkpan(home, release=pinned).executable == str(link_executable(home))


def test_a_newer_pin_repoints_the_link(tmp_path):
    home = tmp_path / 'home'
    with release_server(['v0.2.0', 'v0.2.1'], MILKPAN.target()) as (release, requests):
        ensure_milkpan(home, release=release('v0.2.0'))
        newer = release('v0.2.1')
        client = ensure_milkpan(home, release=newer)
        assert manager_state(client, newer, newer.target()) == 'current'
        assert not any('/download/v0.2.1/' in path for path in requests), 'the link updates through milkpan itself'


def test_a_digest_mismatch_leaves_the_link_unchanged(tmp_path):
    home = tmp_path / 'home'
    with release_server(['v0.2.0', 'v0.2.1'], MILKPAN.target()) as (release, _):
        good = release('v0.2.0')
        ensure_milkpan(home, release=good)
        newer = release('v0.2.1')
        tampered = Release(tag=newer.tag, digests={k: '1' * 64 for k in newer.digests},
                           download_base=newer.download_base, github_api=newer.github_api, env=newer.env)
        with pytest.raises(ConfigurationError, match='does not match the pin'):
            ensure_milkpan(home, release=tampered)
        assert manager_state(inspect_milkpan(home, release=good), good, good.target()) == 'current'


def test_consumer_rules_exist_before_first_use(tmp_path):
    home = tmp_path / 'home'
    ensure_consumer_policy(home, 'consumer-abc')
    policy = (home / 'milkpan.toml').read_text(encoding='utf-8')
    assert 'scope = "consumer-abc"' in policy and 'scope = "consumer-abc-candidates"' in policy
    assert f'scope = "{MANAGER_SCOPE}"' in policy
    ensure_consumer_policy(home, 'consumer-def')
    policy = (home / 'milkpan.toml').read_text(encoding='utf-8')
    assert 'consumer-abc' in policy and 'consumer-def' in policy


def test_the_bucket_is_shared_with_plain_milkpan(tmp_path, monkeypatch):
    monkeypatch.delenv('MILKPAN_HOME', raising=False)
    monkeypatch.setattr('pathlib.Path.home', classmethod(lambda cls: tmp_path))
    assert default_home() == tmp_path / '.milkpan'
    monkeypatch.setenv('MILKPAN_HOME', str(tmp_path / 'elsewhere'))
    assert default_home() == tmp_path / 'elsewhere'

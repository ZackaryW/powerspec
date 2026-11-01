"""Powerspec's pinned, verified, self-managed milkpan."""
import hashlib
import io
import tarfile
import zipfile

import pytest

from powerspec.catalog import ConfigurationError, MetadataUnavailable
from powerspec.milkpan_binary import (MILKPAN, MANAGER_SCOPE, TARGETS, Release, default_home, download,
                                      ensure_consumer_policy,
                                      ensure_milkpan, extract, inspect_milkpan, link_executable, link_state)

from powerspec.milkpan_client import Milkpan

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
    with release_server(['v0.3.0'], MILKPAN.target()) as (release, _):
        pinned = release('v0.3.0')
        name, digest = pinned.asset(pinned.target())
        url = f'{pinned.download_base}/v0.3.0/{name}'
        with pytest.raises(ConfigurationError, match='checksum mismatch'):
            download(url, tmp_path / name, '0' * 64)
        assert not (tmp_path / name).exists()
        download(url, tmp_path / name, digest)
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == digest


def manager_digests(home, release):
    client = Milkpan(link_executable(home), home, env=release.client_env())
    return {lease['digest'] for lease in client.leases(scope=MANAGER_SCOPE)}


def test_bootstrap_links_and_later_runs_reuse_without_download(tmp_path):
    home = tmp_path / 'home'
    with release_server(['v0.3.0'], MILKPAN.target()) as (release, requests):
        pinned = release('v0.3.0')
        with pytest.raises(MetadataUnavailable):
            inspect_milkpan(home, release=pinned)
        assert requests == [], 'inspect never downloads'
        assert link_state(home, pinned) == 'absent'
        client = ensure_milkpan(home, release=pinned)
        assert client.executable == str(link_executable(home))
        assert link_state(home, pinned) == 'supported'
        assert manager_digests(home, pinned) == set(pinned.digests.values())
        before = len(requests)
        ensure_milkpan(home, release=pinned)
        assert len(requests) == before, 'a supported link needs no network'
        assert inspect_milkpan(home, release=pinned).executable == str(link_executable(home))


def test_a_compatible_link_is_reused_even_when_the_pin_differs(tmp_path):
    home = tmp_path / 'home'
    with release_server(['v0.3.0', 'v0.3.1'], MILKPAN.target()) as (release, requests):
        installed = release('v0.3.0')
        ensure_milkpan(home, release=installed)
        before = len(requests)
        ensure_milkpan(home, release=release('v0.3.1'))
        assert len(requests) == before, 'a supported milkpan is never replaced'
        assert manager_digests(home, installed) == set(installed.digests.values())


def test_an_unsupported_link_is_repointed_through_itself(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    with release_server(['v0.3.0', 'v0.3.1'], MILKPAN.target()) as (release, requests):
        ensure_milkpan(home, release=release('v0.3.0'))
        monkeypatch.setattr('powerspec.milkpan_binary.SUPPORTED_LINES', {(9, 9)})
        assert link_state(home, release('v0.3.0')) == 'unsupported'
        newer = release('v0.3.1')
        ensure_milkpan(home, release=newer)
        assert manager_digests(home, newer) == set(newer.digests.values())
        assert not any('/download/v0.3.1/' in path for path in requests), 'the link updates through milkpan itself'


def test_a_digest_mismatch_leaves_the_link_unchanged(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    with release_server(['v0.3.0', 'v0.3.1'], MILKPAN.target()) as (release, _):
        good = release('v0.3.0')
        ensure_milkpan(home, release=good)
        monkeypatch.setattr('powerspec.milkpan_binary.SUPPORTED_LINES', {(9, 9)})
        newer = release('v0.3.1')
        tampered = Release(tag=newer.tag, digests={k: '1' * 64 for k in newer.digests},
                           download_base=newer.download_base, github_api=newer.github_api, env=newer.env)
        with pytest.raises(ConfigurationError, match='does not match the pin'):
            ensure_milkpan(home, release=tampered)
        assert manager_digests(home, good) == set(good.digests.values())


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


USER_RULES = '''# my own rules
[[rule]]
scope = "ci"
effect = "allow"
actions = ["acquire"]
resources = ["github:octo/*"]
'''


def test_the_policy_block_preserves_user_rules_byte_for_byte(tmp_path):
    home = tmp_path / 'home'
    home.mkdir()
    (home / 'milkpan.toml').write_text(USER_RULES, encoding='utf-8')
    ensure_consumer_policy(home, 'powerspec/consumer-abc')
    first = (home / 'milkpan.toml').read_text(encoding='utf-8')
    assert first.startswith(USER_RULES)
    assert 'scope = "powerspec/consumer-abc"' in first and 'scope = "default"' in first
    ensure_consumer_policy(home, 'powerspec/consumer-def')
    second = (home / 'milkpan.toml').read_text(encoding='utf-8')
    assert second.startswith(USER_RULES) and second.count('# >>> powerspec') == 1
    assert 'consumer-abc' in second and 'consumer-def' in second
    ensure_consumer_policy(home, 'powerspec/consumer-def')
    assert (home / 'milkpan.toml').read_text(encoding='utf-8') == second, 'repeated writes are idempotent'


def test_user_default_rules_suppress_the_block_default(tmp_path):
    home = tmp_path / 'home'
    home.mkdir()
    (home / 'milkpan.toml').write_text(USER_RULES.replace('"ci"', '"default"'), encoding='utf-8')
    ensure_consumer_policy(home, 'powerspec/consumer-abc')
    block = (home / 'milkpan.toml').read_text(encoding='utf-8').split('# >>> powerspec')[1]
    assert 'scope = "default"' not in block


@pytest.mark.parametrize('broken', ['# >>> powerspec (managed; edits inside this block are replaced) >>>\n',
                                    '# <<< powerspec <<<\n# >>> powerspec (managed; edits inside this block are replaced) >>>\n'])
def test_malformed_markers_are_rejected(tmp_path, broken):
    home = tmp_path / 'home'
    home.mkdir()
    (home / 'milkpan.toml').write_text(USER_RULES + broken, encoding='utf-8')
    with pytest.raises(ConfigurationError, match='malformed managed block'):
        ensure_consumer_policy(home, 'powerspec/consumer-abc')
    assert (home / 'milkpan.toml').read_text(encoding='utf-8') == USER_RULES + broken

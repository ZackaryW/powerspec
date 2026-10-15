from datetime import timedelta
from pathlib import Path

import pytest
from saucepan_sdk import Saucepan
from zuu.case16 import Candidate, ResolutionSource
from zuu.case17 import ManagedReleaseBinaryError

from powerspec.catalog import ConfigurationError
from powerspec.saucepan_tool import (
    SAUCEPAN_CLI_LINES,
    _managed_saucepan,
    ensure_saucepan_binary,
    inspect_saucepan_binary,
)


def test_manager_uses_supported_cli_lines_and_zuu_release_lifecycle(tmp_path):
    destination = tmp_path / "bin" / "saucepan.exe"

    managed = _managed_saucepan(destination)

    assert managed.destination == destination
    assert managed.resolver.owner == "ZackaryW"
    assert managed.resolver.repository == "saucepan"
    assert managed.max_age == timedelta(hours=24)
    assert managed.policy_id == "saucepan-cli-0.9-zip-v1"
    assert managed.state_store.path == destination.with_name("saucepan-check.json")
    assert SAUCEPAN_CLI_LINES == {(0, 9)}
    assert managed.is_compatible("0.9.1")
    assert managed.is_compatible("0.9.0")
    assert not managed.is_compatible("0.7.0")
    assert managed.resolver.candidate_filter(
        Candidate("v0.9.0", ResolutionSource.RELEASE)
    )
    assert not managed.resolver.candidate_filter(
        Candidate("v0.7.0", ResolutionSource.RELEASE)
    )


def test_ensure_creates_parent_and_returns_zuu_destination(tmp_path, monkeypatch):
    destination = tmp_path / "new" / "bin" / "saucepan.exe"
    calls = []

    class Manager:
        def ensure(self, **kwargs):
            calls.append(destination.parent.is_dir())
            return type("Result", (), {"destination": destination})()

    monkeypatch.setattr("powerspec.saucepan_tool._managed_saucepan", lambda target: Manager())

    assert ensure_saucepan_binary(destination) == destination
    assert calls == [True]


def test_ensure_translates_missing_usable_binary_to_configuration_error(tmp_path, monkeypatch):
    class Manager:
        def ensure(self, **kwargs):
            raise ManagedReleaseBinaryError("could not produce a usable binary")

    monkeypatch.setattr("powerspec.saucepan_tool._managed_saucepan", lambda target: Manager())

    with pytest.raises(ConfigurationError, match="cannot install or update Saucepan"):
        ensure_saucepan_binary(tmp_path / "bin" / "saucepan.exe")


def test_inspect_requires_existing_compatible_binary_without_creating_parent(tmp_path, monkeypatch):
    destination = tmp_path / "missing" / "saucepan.exe"
    with pytest.raises(ConfigurationError, match="not installed"):
        inspect_saucepan_binary(destination)
    assert not destination.parent.exists()

    destination.parent.mkdir()
    destination.write_bytes(b"binary")
    monkeypatch.setattr("powerspec.saucepan_tool._probe", lambda path: "0.9.0")
    monkeypatch.setattr("powerspec.saucepan_tool._validate", lambda path, tag: None)
    assert inspect_saucepan_binary(destination) == destination


def test_default_source_client_lazily_uses_ensured_binary(tmp_path, monkeypatch):
    from powerspec import sources

    destination = tmp_path / "saucepan.exe"
    calls = []
    monkeypatch.setattr(
        sources,
        "ensure_saucepan_binary",
        lambda: calls.append("ensure") or destination,
    )

    store = sources.SaucepanSources()
    assert calls == []

    client = store._client_or_default()

    assert isinstance(client, Saucepan)
    assert client.binary == str(destination)
    assert store._client_or_default() is client
    assert calls == ["ensure"]


def test_read_only_source_client_lazily_inspects_existing_binary(tmp_path, monkeypatch):
    from powerspec import sources

    destination = tmp_path / "saucepan.exe"
    calls = []
    monkeypatch.setattr(
        sources,
        "inspect_saucepan_binary",
        lambda: calls.append("inspect") or destination,
    )
    monkeypatch.setattr(
        sources,
        "ensure_saucepan_binary",
        lambda: (_ for _ in ()).throw(AssertionError("read-only lookup managed the binary")),
    )
    client = sources.SaucepanSources(manage_binary=False)._client_or_default()
    assert client.binary == str(destination) and calls == ["inspect"]


def test_explicit_source_client_bypasses_managed_binary(monkeypatch):
    from powerspec import sources

    client = object()
    monkeypatch.setattr(
        sources,
        "ensure_saucepan_binary",
        lambda: (_ for _ in ()).throw(AssertionError("managed lifecycle must not run")),
    )

    assert sources.SaucepanSources(client)._client is client


def test_readonly_binary_probes_share_budget(tmp_path, monkeypatch):
    import powerspec.saucepan_tool as module
    from types import SimpleNamespace
    clock = [1.0]
    calls = []
    destination = tmp_path / 'saucepan.exe'
    destination.write_bytes(b'fixture')
    monkeypatch.setattr(module, 'monotonic', lambda: clock[0])
    def inspect(argv, **options):
        calls.append((argv[-1], options['timeout']))
        clock[0] += .3
        return SimpleNamespace(ok=True, version='0.9.0', stdout='register-application register-source prepare-group pin inspect')
    monkeypatch.setattr(module, 'inspect_executable', inspect)
    assert inspect_saucepan_binary(destination, deadline=2) == destination
    assert [x[0] for x in calls] == ['--version', '--help']
    assert [x[1] for x in calls] == pytest.approx([1, .7])


def test_zip_assets_select_manager_platform_and_exclude_sdk():
    from zuu.case16 import ReleaseAsset
    from powerspec.saucepan_tool import _select_manager_zip
    assets = tuple(ReleaseAsset(name, 'https://example.test/' + name) for name in (
        'saucepan-x86_64-pc-windows-msvc.zip', 'saucepan-aarch64-apple-darwin.zip',
        'saucepan-sdk-0.1.0.zip'))
    assert _select_manager_zip(assets, 'Windows', 'AMD64') == assets[0]
    assert _select_manager_zip(assets, 'Darwin', 'arm64') == assets[1]


def test_zip_download_reads_only_exact_manager(tmp_path, monkeypatch):
    import io
    import os
    import zipfile
    from powerspec.saucepan_tool import _download_manager
    stream = io.BytesIO()
    name = 'saucepan.exe' if os.name == 'nt' else 'saucepan'
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr(name, b'manager')
        archive.writestr('saucepan-shim.exe', b'shim')
        archive.writestr('../outside', b'never extracted')
    monkeypatch.setattr('urllib.request.urlopen', lambda *a, **k: io.BytesIO(stream.getvalue()))
    target = tmp_path / 'stage'
    _download_manager('https://example.test/archive.zip', target)
    assert target.read_bytes() == b'manager'
    assert list(tmp_path.iterdir()) == [target]

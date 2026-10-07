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
    assert managed.policy_id == "saucepan-cli-0.5-0.6-v1"
    assert managed.state_store.path == destination.with_name("saucepan-check.json")
    assert SAUCEPAN_CLI_LINES == {(0, 5), (0, 6)}
    assert managed.is_compatible("0.5.9")
    assert managed.is_compatible("0.6.0")
    assert not managed.is_compatible("0.7.0")
    assert managed.resolver.candidate_filter(
        Candidate("v0.6.0", ResolutionSource.RELEASE)
    )
    assert not managed.resolver.candidate_filter(
        Candidate("v0.7.0", ResolutionSource.RELEASE)
    )


def test_ensure_creates_parent_and_returns_zuu_destination(tmp_path, monkeypatch):
    destination = tmp_path / "new" / "bin" / "saucepan.exe"
    calls = []

    class Manager:
        def ensure(self):
            calls.append(destination.parent.is_dir())
            return type("Result", (), {"destination": destination})()

    monkeypatch.setattr("powerspec.saucepan_tool._managed_saucepan", lambda target: Manager())

    assert ensure_saucepan_binary(destination) == destination
    assert calls == [True]


def test_ensure_translates_missing_usable_binary_to_configuration_error(tmp_path, monkeypatch):
    class Manager:
        def ensure(self):
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
    monkeypatch.setattr("powerspec.saucepan_tool._probe", lambda path: "0.5.0")
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
        return SimpleNamespace(ok=True, version='0.6.0')
    monkeypatch.setattr(module, 'inspect_executable', inspect)
    assert inspect_saucepan_binary(destination, deadline=2) == destination
    assert [x[0] for x in calls] == ['--version', '--help']
    assert [x[1] for x in calls] == pytest.approx([1, .7])

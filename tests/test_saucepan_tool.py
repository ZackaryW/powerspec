from datetime import timedelta
from pathlib import Path

import pytest
from saucepan_sdk import Saucepan
from zuu.case16 import Candidate, ResolutionSource
from zuu.case17 import ManagedReleaseBinaryError

from powerspec.catalog import ConfigurationError
from powerspec.saucepan_tool import (
    SAUCEPAN_SDK_LINE,
    _managed_saucepan,
    ensure_saucepan_binary,
)


def test_manager_uses_sdk_line_shared_policy_and_zuu_release_lifecycle(tmp_path):
    destination = tmp_path / "bin" / "saucepan.exe"

    managed = _managed_saucepan(destination)

    assert managed.destination == destination
    assert managed.resolver.owner == "ZackaryW"
    assert managed.resolver.repository == "saucepan"
    assert managed.max_age == timedelta(hours=24)
    assert managed.policy_id == f"saucepan-sdk-{'.'.join(map(str, SAUCEPAN_SDK_LINE))}-v1"
    assert managed.state_store.path == destination.with_name("saucepan-check.json")
    compatible = ".".join(map(str, (*SAUCEPAN_SDK_LINE, 9)))
    incompatible = f"{SAUCEPAN_SDK_LINE[0]}.{SAUCEPAN_SDK_LINE[1] + 1}.0"
    assert managed.is_compatible(compatible)
    assert not managed.is_compatible(incompatible)
    assert managed.resolver.candidate_filter(
        Candidate(f"v{compatible}", ResolutionSource.RELEASE)
    )
    assert not managed.resolver.candidate_filter(
        Candidate(f"v{incompatible}", ResolutionSource.RELEASE)
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


def test_explicit_source_client_bypasses_managed_binary(monkeypatch):
    from powerspec import sources

    client = object()
    monkeypatch.setattr(
        sources,
        "ensure_saucepan_binary",
        lambda: (_ for _ in ()).throw(AssertionError("managed lifecycle must not run")),
    )

    assert sources.SaucepanSources(client)._client is client

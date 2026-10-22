from saucepan_sdk import Client
from pathlib import Path


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

    assert isinstance(client, Client)
    assert store._executable == destination
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
    assert isinstance(client, Client) and calls == ["inspect"]


def test_explicit_source_client_bypasses_managed_binary(monkeypatch):
    from powerspec import sources

    client = object()
    monkeypatch.setattr(
        sources,
        "ensure_saucepan_binary",
        lambda: (_ for _ in ()).throw(AssertionError("managed lifecycle must not run")),
    )

    assert sources.SaucepanSources(client)._client is client


def test_default_client_binds_the_inspected_root_not_ambient_root(tmp_path, monkeypatch):
    from powerspec import sources
    from powerspec.saucepan_tool import saucepan_executable_path
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: tmp_path))
    monkeypatch.delenv('POWERSPEC_SAUCEPAN', raising=False)
    monkeypatch.setenv('SAUCEPAN_ROOT', str(tmp_path / 'other-store'))
    target = saucepan_executable_path()
    monkeypatch.setattr(sources, 'ensure_saucepan_binary', lambda: target)
    calls = []
    monkeypatch.setattr(sources, 'Client', lambda **kwargs: calls.append(kwargs) or object())
    sources.SaucepanSources()._client_or_default()
    assert calls[0]['root'] == str(target.parent.parent)

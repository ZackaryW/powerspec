from pathlib import Path
from types import MappingProxyType

import pytest
from saucepan_sdk import SaucepanError

from powerspec.catalog import ConfigurationError
from powerspec.sources import ExternalCatalogs, SaucepanSources, SourceBinding, discover_catalogs


SOURCE = {"provider": "git", "origin": "https://example.test/team/tools", "reference": "main"}


def test_lookup_passes_one_remaining_budget_to_each_public_sdk_call(tmp_path, monkeypatch):
    import powerspec.sources as sources
    import powerspec.saucepan_tool as binary
    clock = [10.0]
    calls = []
    app = App(tmp_path)
    monkeypatch.setattr(binary, 'monotonic', lambda: clock[0])
    def inspect(*, deadline):
        assert deadline == 11
        clock[0] += .2
        calls.append('inspect')
        return tmp_path / 'saucepan.exe'
    class SDK:
        def __init__(self, *, binary, timeout=None):
            self.binary = binary
            self.timeout = timeout
        def for_app(self, name):
            assert name == 'powerspec'
            return self
        def __getattr__(self, method):
            def run(*args):
                calls.append((method, self.timeout))
                clock[0] += .2
                return getattr(app, method)(*args)
            return run
    monkeypatch.setattr(sources, 'inspect_saucepan_binary', inspect)
    monkeypatch.setattr(sources, 'Saucepan', SDK)
    monkeypatch.setattr(sources, 'ensure_saucepan_binary', lambda: pytest.fail('acquisition'))
    store = SaucepanSources(manage_binary=False)
    assert store.lookup('tools', SOURCE, deadline=11).root == tmp_path
    assert calls[0] == 'inspect'
    assert [c[0] for c in calls[1:]] == ['view', 'history', 'path']
    assert [c[1] for c in calls[1:]] == pytest.approx([.8, .6, .4])
    assert app.acquire_calls == []


def test_stalled_source_subprocess_is_bounded_without_retry(tmp_path, monkeypatch):
    import subprocess
    import sys
    import time
    import saucepan_sdk._runner as runner
    import powerspec.sources as sources
    from powerspec.catalog import MetadataUnavailable
    real_run = subprocess.run
    calls = []
    def stalled(argv, **kwargs):
        calls.append(kwargs['timeout'])
        return real_run([sys.executable, '-c', 'import time;time.sleep(10)'], **kwargs)
    monkeypatch.setattr(runner.subprocess, 'run', stalled)
    monkeypatch.setattr(sources, 'inspect_saucepan_binary', lambda **kw: tmp_path / 'saucepan.exe')
    start = time.monotonic()
    with pytest.raises(MetadataUnavailable, match='unavailable'):
        SaucepanSources(manage_binary=False).lookup('tools', SOURCE, deadline=start + .15)
    assert time.monotonic() - start < 1.5
    assert len(calls) == 1 and 0 < calls[0] <= .15


def artifact(root: Path, *, folder=None, revision="a" * 40, snapshot="snap", source=SOURCE):
    return {
        "id": "artifact-" + (folder or "root"),
        "source_id": "1" * 64,
        "source": source,
        "snapshot_id": snapshot,
        "revision": revision,
        "folder": folder,
    }


class App:
    def __init__(self, root: Path, *, entries=None, fail=None, source=SOURCE):
        self.root = root
        self.source = source
        self.entries = entries if entries is not None else {"root": artifact(root, source=source)}
        self.fail = fail
        self.acquire_calls = []

    def view(self):
        if self.fail == "view":
            raise OSError("view unavailable")
        return {"version": 1, "app": "powerspec", "entries": self.entries}

    def history(self, source_id):
        if self.fail == "history":
            raise OSError("history unavailable")
        return {"source": self.source, "current": {"id": "snap", "revision": "a" * 40}}

    def path(self, artifact_id):
        return str(self.root)

    def acquire(self, recipe):
        self.acquire_calls.append(recipe)
        if self.fail == "acquire":
            raise OSError("network unavailable")
        return {"artifact": artifact(self.root, revision="b" * 40, source=self.source),
                "directory": str(self.root), "content_verified": True}


class Client:
    def __init__(self, app, *, store=True, registered=True, missing="store index is missing"):
        self.app = app
        self.store = store
        self.registered = registered
        self.missing = missing
        self.names = []
        self.init_calls = 0
        self.register_calls = []

    def for_app(self, name):
        self.names.append(name)
        client = self

        class Selected:
            def __getattr__(self, attribute):
                if attribute == "view":
                    def view():
                        if not client.store:
                            raise SaucepanError(client.missing, stderr=client.missing)
                        if not client.registered:
                            raise SaucepanError("app is not registered", stderr="app is not registered")
                        return client.app.view()
                    return view
                return getattr(client.app, attribute)

        return Selected()

    def init(self):
        self.init_calls += 1
        self.store = True
        return {"created": True}

    def register(self, name):
        self.register_calls.append(name)
        self.registered = True
        return {"version": 1, "app": name, "token": []}


def test_lookup_is_read_only_and_retains_provenance(tmp_path):
    app = App(tmp_path)
    client = Client(app)
    result = SaucepanSources(client).lookup("tools", SOURCE)
    assert result.identity == "tools"
    assert result.repository == SOURCE["origin"]
    assert result.requested_revision == "main"
    assert result.resolved_revision == "a" * 40
    assert result.source_id == "1" * 64
    assert result.root == tmp_path.resolve()
    assert app.acquire_calls == []
    assert client.names == ["powerspec"]


def test_lookup_accepts_frozen_profile_recipe(tmp_path):
    result = SaucepanSources(Client(App(tmp_path))).lookup(
        "tools", MappingProxyType(SOURCE)
    )
    assert result.repository == SOURCE["origin"]


def test_acquire_refreshes_registered_recipe_and_returns_complete_root(tmp_path):
    app = App(tmp_path)
    result = SaucepanSources(Client(app)).acquire("tools", SOURCE)
    assert app.acquire_calls == [{"source": SOURCE}]
    assert result.resolved_revision == "b" * 40
    assert result.root == tmp_path.resolve()


@pytest.mark.parametrize("identity", ["builtin", "Bad Name", ""])
def test_reserved_or_invalid_identity_is_rejected_without_sdk_call(tmp_path, identity):
    client = Client(App(tmp_path))
    with pytest.raises(ConfigurationError, match="invalid or reserved"):
        SaucepanSources(client).lookup(identity, SOURCE)
    assert client.names == []


def test_lookup_requires_declared_recipe_and_full_current_artifact(tmp_path):
    empty = App(tmp_path, entries={})
    with pytest.raises(ConfigurationError, match="no current materialization"):
        SaucepanSources(Client(empty)).lookup("tools", SOURCE)

    entries = {"folder": artifact(tmp_path, folder="skills")}
    with pytest.raises(ConfigurationError, match="no unique full-repository"):
        SaucepanSources(Client(App(tmp_path, entries=entries))).lookup("tools", SOURCE)

    other = artifact(tmp_path)
    other["id"] = "second"
    other["source_id"] = "2" * 64
    other["source"] = {**SOURCE, "origin": "https://example.test/other"}
    result = SaucepanSources(Client(App(tmp_path, entries={"one": artifact(tmp_path), "two": other}))).lookup(
        "tools", SOURCE
    )
    assert result.source_id == "1" * 64


def test_failed_refresh_reports_failure_without_replacing_prior_lookup(tmp_path):
    app = App(tmp_path)
    sources = SaucepanSources(Client(app))
    before = sources.lookup("tools", SOURCE)
    app.fail = "acquire"
    with pytest.raises(ConfigurationError, match="failed to acquire.*network unavailable"):
        sources.acquire("tools", SOURCE)
    app.fail = None
    assert sources.lookup("tools", SOURCE) == before


def test_ensure_reuses_existing_recipe_without_refresh(tmp_path):
    app = App(tmp_path)
    client = Client(app)
    result = SaucepanSources(client).ensure("tools", SOURCE)
    assert result.resolved_revision == "a" * 40
    assert app.acquire_calls == []
    assert client.init_calls == 0 and client.register_calls == []


def test_remote_git_suffix_is_treated_as_the_same_declared_origin(tmp_path):
    canonical = {**SOURCE, "origin": SOURCE["origin"] + ".git"}
    result = SaucepanSources(Client(App(tmp_path, source=canonical))).lookup("tools", SOURCE)
    assert result.repository == SOURCE["origin"]


@pytest.mark.parametrize("missing", ["store index is missing", "store secret is missing"])
def test_ensure_initializes_registers_and_acquires_missing_recipe(tmp_path, missing):
    app = App(tmp_path, entries={})
    client = Client(app, store=False, registered=False, missing=missing)
    result = SaucepanSources(client).ensure("tools", SOURCE)
    assert result.resolved_revision == "b" * 40
    assert client.init_calls == 1
    assert client.register_calls == ["powerspec"]
    assert app.acquire_calls == [{"source": SOURCE}]


def test_missing_secret_does_not_bypass_saucepan_initialization_guard(tmp_path):
    app = App(tmp_path, entries={})
    client = Client(app, store=False, registered=False, missing="store secret is missing")

    def reject_existing_store():
        raise SaucepanError("existing store data prevents initialization")

    client.init = reject_existing_store
    with pytest.raises(ConfigurationError, match="cannot initialize Saucepan store.*existing store data"):
        SaucepanSources(client).ensure("tools", SOURCE)
    assert client.register_calls == []
    assert app.acquire_calls == []


def binding(identity, root, revision="a" * 40):
    return SourceBinding(identity, "https://example.test/tools", "main", revision,
                         "1" * 64, "artifact", root)


def write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_catalog_discovery_includes_nested_reusable_roots_and_excludes_consumers(tmp_path):
    public = tmp_path / ".pspec"
    nested = tmp_path / "packages/tool/.pspec"
    private = tmp_path / "openspec/.pspec"
    for root in (public, nested, private):
        write(root, "profiles/base.toml", 'scope="user"')
    assert discover_catalogs(tmp_path) == (public.resolve(), nested.resolve())


def test_catalog_discovery_rejects_absence_and_escape(tmp_path):
    with pytest.raises(ConfigurationError, match="no reusable"):
        discover_catalogs(tmp_path)
    outside = tmp_path.parent / "external-catalog"
    write(outside, "profiles/base.toml", 'scope="user"')
    link = tmp_path / ".pspec"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(str(error))
    with pytest.raises(ConfigurationError, match="escapes"):
        discover_catalogs(tmp_path)


def test_external_registration_is_validated_atomic_and_reserves_builtin(tmp_path):
    good = tmp_path / "good"
    write(good, ".pspec/profiles/base.toml", 'scope="user"')
    registry = ExternalCatalogs().register(binding("team", good))
    assert tuple(registry.bindings) == ("team",)

    bad = tmp_path / "bad"
    write(bad, ".pspec/profiles/base.toml", 'scope="broken"')
    with pytest.raises(ConfigurationError, match="base.toml"):
        registry.register(binding("team", bad, "b" * 40))
    assert registry.bindings["team"].source.root == good

    absent = tmp_path / "absent"
    absent.mkdir()
    with pytest.raises(ConfigurationError, match="no reusable"):
        registry.register(binding("team", absent))
    assert registry.bindings["team"].source.root == good

    with pytest.raises(ConfigurationError, match="reserved"):
        registry.register(binding("builtin", good))

from pathlib import Path

import pytest

from powerspec.catalog import ConfigurationError
from powerspec.sources import SaucepanSources


SOURCE = {"provider": "git", "origin": "https://example.test/team/tools", "reference": "main"}


def artifact(root: Path, *, folder=None, revision="a" * 40, snapshot="snap"):
    return {
        "id": "artifact-" + (folder or "root"),
        "source_id": "1" * 64,
        "source": SOURCE,
        "snapshot_id": snapshot,
        "revision": revision,
        "folder": folder,
    }


class App:
    def __init__(self, root: Path, *, entries=None, fail=None):
        self.root = root
        self.entries = entries if entries is not None else {"root": artifact(root)}
        self.fail = fail
        self.acquire_calls = []

    def view(self):
        if self.fail == "view":
            raise OSError("view unavailable")
        return {"version": 1, "app": "tools", "entries": self.entries}

    def history(self, source_id):
        if self.fail == "history":
            raise OSError("history unavailable")
        return {"source": SOURCE, "current": {"id": "snap", "revision": "a" * 40}}

    def path(self, artifact_id):
        return str(self.root)

    def acquire(self, recipe):
        self.acquire_calls.append(recipe)
        if self.fail == "acquire":
            raise OSError("network unavailable")
        return {"artifact": artifact(self.root, revision="b" * 40),
                "directory": str(self.root), "content_verified": True}


class Client:
    def __init__(self, app):
        self.app = app
        self.names = []

    def for_app(self, name):
        self.names.append(name)
        return self.app


def test_lookup_is_read_only_and_retains_provenance(tmp_path):
    app = App(tmp_path)
    client = Client(app)
    result = SaucepanSources(client).lookup("tools")
    assert result.identity == "tools"
    assert result.repository == SOURCE["origin"]
    assert result.requested_revision == "main"
    assert result.resolved_revision == "a" * 40
    assert result.source_id == "1" * 64
    assert result.root == tmp_path.resolve()
    assert app.acquire_calls == []
    assert client.names == ["tools"]


def test_acquire_refreshes_registered_recipe_and_returns_complete_root(tmp_path):
    app = App(tmp_path)
    result = SaucepanSources(Client(app)).acquire("tools")
    assert app.acquire_calls == [{"source": SOURCE}]
    assert result.resolved_revision == "b" * 40
    assert result.root == tmp_path.resolve()


@pytest.mark.parametrize("identity", ["builtin", "Bad Name", ""])
def test_reserved_or_invalid_identity_is_rejected_without_sdk_call(tmp_path, identity):
    client = Client(App(tmp_path))
    with pytest.raises(ConfigurationError, match="invalid or reserved"):
        SaucepanSources(client).lookup(identity)
    assert client.names == []


def test_lookup_requires_one_git_source_and_full_current_artifact(tmp_path):
    empty = App(tmp_path, entries={})
    with pytest.raises(ConfigurationError, match="no touched Git source"):
        SaucepanSources(Client(empty)).lookup("tools")

    entries = {"folder": artifact(tmp_path, folder="skills")}
    with pytest.raises(ConfigurationError, match="no unique full-repository"):
        SaucepanSources(Client(App(tmp_path, entries=entries))).lookup("tools")

    other = artifact(tmp_path)
    other["id"] = "second"
    other["source_id"] = "2" * 64
    other["source"] = {**SOURCE, "origin": "https://example.test/other"}
    with pytest.raises(ConfigurationError, match="ambiguous"):
        SaucepanSources(Client(App(tmp_path, entries={"one": artifact(tmp_path), "two": other}))).lookup("tools")


def test_failed_refresh_reports_failure_without_replacing_prior_lookup(tmp_path):
    app = App(tmp_path)
    sources = SaucepanSources(Client(app))
    before = sources.lookup("tools")
    app.fail = "acquire"
    with pytest.raises(ConfigurationError, match="failed to acquire.*network unavailable"):
        sources.acquire("tools")
    app.fail = None
    assert sources.lookup("tools") == before

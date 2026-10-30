"""Multi-project Antigravity guidance names a stored workset default."""
from pathlib import Path

import pytest

from powerspec.workset_defaults import record_for, store
from powerspec.workset_openspec import Member, Workset
from tests.test_hook_antigravity import INTRO, agy, consumer_at, injected, payload

FALLBACK = "If you cannot determine which project applies, use the default project"


@pytest.fixture
def defaults(tmp_path, monkeypatch):
    import powerspec.workset_defaults as module
    from powerspec.workset_openspec import OpenSpec
    path = tmp_path / ".powerspec/worksets.toml"
    monkeypatch.setattr(module, "defaults_file", lambda: path)
    monkeypatch.setattr(OpenSpec, "call", lambda *a, **k: pytest.fail("hook must not invoke OpenSpec"))
    return path


def workset(*roots):
    return Workset("ws", tuple(Member(root.name, root) for root in roots))


def test_matching_session_names_the_default_and_marks_its_section(tmp_path, monkeypatch, defaults):
    api = consumer_at(tmp_path / "api", "API rules.")
    central = consumer_at(tmp_path / "central", "Central rules.")
    store(defaults, {"ws": record_for(workset(api, central), "central")})

    result = agy(monkeypatch, tmp_path, payload(api, central))

    text = injected(result.stdout)
    intro = text.split("\n\n")[0]
    assert intro.startswith(INTRO) and f"{FALLBACK} central" in intro
    assert f"### central ({central}) (default)" in text
    assert f"### api ({api})\n" in text


def test_default_without_guidance_is_named_without_an_empty_section(tmp_path, monkeypatch, defaults):
    api = consumer_at(tmp_path / "api", "API rules.")
    plain = tmp_path / "plain"
    plain.mkdir()
    store(defaults, {"ws": record_for(workset(api, plain), "plain")})

    text = injected(agy(monkeypatch, tmp_path, payload(api, plain)).stdout)

    assert f"{FALLBACK} plain" in text.split("\n\n")[0]
    assert "### plain" not in text


@pytest.mark.parametrize("stored", ["none", "subset"])
def test_no_matching_default_keeps_plain_delegation(tmp_path, monkeypatch, defaults, stored):
    api = consumer_at(tmp_path / "api", "API rules.")
    web = consumer_at(tmp_path / "web", "Web rules.")
    if stored == "subset":
        store(defaults, {"ws": record_for(workset(api), "api")})

    result = agy(monkeypatch, tmp_path, payload(api, web))

    assert FALLBACK not in injected(result.stdout)
    assert "(default)" not in result.stdout
    assert result.stderr == ""


def test_malformed_defaults_file_warns_and_still_delivers(tmp_path, monkeypatch, defaults):
    api = consumer_at(tmp_path / "api", "API rules.")
    web = consumer_at(tmp_path / "web", "Web rules.")
    defaults.parent.mkdir(parents=True)
    defaults.write_text("[worksets", encoding="utf-8")

    result = agy(monkeypatch, tmp_path, payload(api, web))

    assert result.exit_code == 0
    assert "API rules." in injected(result.stdout) and FALLBACK not in result.stdout
    assert "worksets.toml" in result.stderr


def test_two_matching_snapshots_name_no_default(tmp_path, monkeypatch, defaults):
    api = consumer_at(tmp_path / "api", "API rules.")
    web = consumer_at(tmp_path / "web", "Web rules.")
    store(defaults, {"a": record_for(workset(api, web), "api"), "b": record_for(workset(api, web), "web")})

    result = agy(monkeypatch, tmp_path, payload(api, web))

    assert FALLBACK not in injected(result.stdout)
    assert "ambiguous" in result.stderr

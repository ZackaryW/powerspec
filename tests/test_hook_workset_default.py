"""A stored workset default selects the only guidance a multi-project session receives."""
from pathlib import Path

import pytest

from powerspec.workset_defaults import record_for, store
from powerspec.workset_openspec import Member, Workset
from tests.test_hook_antigravity import COMMAND, INTRO, agy, consumer_at, injected, payload

DEFAULT = "The default project is"


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


def test_matching_default_delivers_only_its_guidance(tmp_path, monkeypatch, defaults):
    api = consumer_at(tmp_path / "api", "API rules.")
    central = consumer_at(tmp_path / "central", "Central rules.")
    store(defaults, {"ws": record_for(workset(api, central), "central")})

    result = agy(monkeypatch, tmp_path, payload(api, central))

    text = injected(result.stdout)
    assert text.startswith(INTRO) and COMMAND in text and f"{DEFAULT} central (" in text
    assert f"- central ({central}) (default)" in text and f"- api ({api})\n" in text + "\n"
    assert text.endswith(f"### central ({central})\n\nCentral rules.")
    assert "API rules." not in text


def test_default_without_guidance_is_named_without_a_section(tmp_path, monkeypatch, defaults):
    api = consumer_at(tmp_path / "api", "API rules.")
    web = consumer_at(tmp_path / "web", "Web rules.")
    plain = tmp_path / "plain"
    plain.mkdir()
    store(defaults, {"ws": record_for(workset(api, web, plain), "plain")})

    text = injected(agy(monkeypatch, tmp_path, payload(api, web, plain)).stdout)

    assert f"{DEFAULT} plain" in text
    assert "###" not in text and "API rules." not in text and "Web rules." not in text


def test_default_whose_guidance_fails_still_delivers_the_list(tmp_path, monkeypatch, defaults):
    import powerspec.cli.hook as module
    api = consumer_at(tmp_path / "api", "API rules.")
    central = consumer_at(tmp_path / "central", "Central rules.")
    store(defaults, {"ws": record_for(workset(api, central), "central")})

    def broken(root, cwd, *args):
        raise module.ConfigurationError("trait is malformed")

    monkeypatch.setattr(module, "_guidance", broken)
    result = agy(monkeypatch, tmp_path, payload(api, central))

    assert result.exit_code == 0
    text = injected(result.stdout)
    assert f"{DEFAULT} central" in text and f"- api ({api})" in text and "###" not in text
    assert "trait is malformed" in result.stderr and str(central) in result.stderr


@pytest.mark.parametrize("stored", ["none", "subset"])
def test_no_matching_default_delivers_no_guidance(tmp_path, monkeypatch, defaults, stored):
    api = consumer_at(tmp_path / "api", "API rules.")
    web = consumer_at(tmp_path / "web", "Web rules.")
    if stored == "subset":
        store(defaults, {"ws": record_for(workset(api), "api")})

    result = agy(monkeypatch, tmp_path, payload(api, web))

    text = injected(result.stdout)
    assert DEFAULT not in text and "(default)" not in text and "rules." not in text
    assert result.stderr == ""


def test_malformed_defaults_file_warns_and_still_delivers_the_list(tmp_path, monkeypatch, defaults):
    api = consumer_at(tmp_path / "api", "API rules.")
    web = consumer_at(tmp_path / "web", "Web rules.")
    defaults.parent.mkdir(parents=True)
    defaults.write_text("[worksets", encoding="utf-8")

    result = agy(monkeypatch, tmp_path, payload(api, web))

    assert result.exit_code == 0
    text = injected(result.stdout)
    assert f"- api ({api})" in text and DEFAULT not in text and "rules." not in text
    assert "worksets.toml" in result.stderr


def test_two_matching_snapshots_name_no_default(tmp_path, monkeypatch, defaults):
    api = consumer_at(tmp_path / "api", "API rules.")
    web = consumer_at(tmp_path / "web", "Web rules.")
    store(defaults, {"a": record_for(workset(api, web), "api"), "b": record_for(workset(api, web), "web")})

    result = agy(monkeypatch, tmp_path, payload(api, web))

    text = injected(result.stdout)
    assert DEFAULT not in text and "rules." not in text
    assert "ambiguous" in result.stderr

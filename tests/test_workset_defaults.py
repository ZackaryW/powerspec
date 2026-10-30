import os
from pathlib import Path

import pytest

from powerspec.workset_defaults import (
    DefaultsError, WorksetDefault, load, match, normalize, record_for, staleness, store,
)
from powerspec.workset_openspec import Member, Workset

ROOT = Path("C:/work") if os.name == "nt" else Path("/work")


def workset(name="poc-ab", labels=("central", "server")):
    return Workset(name, tuple(Member(label, ROOT / f"poc ab ({label})") for label in labels))


def test_missing_file_has_no_defaults(tmp_path):
    assert load(tmp_path / "worksets.toml") == {}


def test_round_trip_keeps_other_worksets_and_skips_identical_writes(tmp_path):
    path = tmp_path / ".powerspec/worksets.toml"
    entries = {"poc-ab": record_for(workset(), "central"),
               "other": record_for(workset("other", ("x", "y")), "y")}

    assert store(path, entries) is True
    assert load(path) == entries
    assert store(path, load(path)) is False
    del entries["poc-ab"]
    store(path, entries)
    assert load(path) == {"other": record_for(workset("other", ("x", "y")), "y")}


def test_record_requires_a_member_label():
    with pytest.raises(ValueError, match="central, server"):
        record_for(workset(), "missing")


def test_failed_write_keeps_the_previous_file(tmp_path, monkeypatch):
    import powerspec.workset_defaults as defaults
    from powerspec.utils.atomic import AtomicWriteError
    path = tmp_path / "worksets.toml"
    store(path, {"poc-ab": record_for(workset(), "central")})
    before = path.read_bytes()
    monkeypatch.setattr(defaults, "replace_bytes", lambda *a: (_ for _ in ()).throw(AtomicWriteError("disk")))

    with pytest.raises(AtomicWriteError):
        store(path, {})
    assert path.read_bytes() == before


@pytest.mark.parametrize("text", ["[worksets", "worksets = 1", '[worksets.a]\ndefault = 3\npath = "x"\nmembers = []',
                                  '[worksets.a]\ndefault = "x"\npath = "x"\nmembers = "x"'])
def test_malformed_files_raise_a_typed_error(tmp_path, text):
    path = tmp_path / "worksets.toml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(DefaultsError):
        load(path)


def test_normalization_ignores_separator_trailing_slash_and_case_where_the_os_does():
    base = str(ROOT / "poc ab (central)")
    assert normalize(base) == normalize(base.replace("\\", "/") + "/")
    if os.name == "nt":
        assert normalize("C:\\Work\\App") == normalize("c:/work/app")


def test_matching_requires_the_exact_member_set():
    entries = {"poc-ab": record_for(workset(), "central")}
    members = [str(member.path) for member in workset().members]
    posix = [Path(item).as_posix() for item in members]

    assert match(entries, posix) == ("poc-ab", entries["poc-ab"], ())
    assert match(entries, posix[:1]) == (None, None, ())
    assert match(entries, [*posix, str(ROOT / "extra")]) == (None, None, ())


def test_two_matching_snapshots_are_ambiguous():
    entries = {"a": record_for(workset("a"), "central"), "b": record_for(workset("b"), "server")}
    paths = [str(member.path) for member in workset().members]

    assert match(entries, paths) == (None, None, ("a", "b"))


def test_staleness_reasons():
    entry = record_for(workset(), "central")

    assert staleness(entry, workset()) is None
    assert staleness(entry, None) == "workset removed"
    assert staleness(entry, workset(labels=("server", "web"))) == "label no longer a member"
    assert staleness(entry, workset(labels=("central", "server", "web"))) == "members changed"

import json
import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "hatch_build.py"
SPEC = importlib.util.spec_from_file_location("powerspec_hatch_build", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)
BuildSourceError = BUILD.BuildSourceError
MANIFEST = BUILD.MANIFEST
prepare_snapshot = BUILD.prepare_snapshot


REVISION = "a" * 40
SKILLS = ["openspec-one", "openspec-two"]


def declaration():
    return {
        "owner": "Fission-AI",
        "repository": "OpenSpec",
        "revision": REVISION,
        "license": "LICENSE",
        "skills": SKILLS.copy(),
    }


def source(root: Path):
    (root / "LICENSE").write_text("license\n", encoding="utf-8")
    for name in SKILLS:
        path = root / "skills" / name
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text(f"---\nname: {name}\n---\nbody\n", encoding="utf-8")
        (path / "reference.md").write_text(name, encoding="utf-8")


def test_local_override_materializes_only_complete_declared_skills(tmp_path, monkeypatch):
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    source(upstream)
    (upstream / "skills/unselected").mkdir()
    (upstream / "skills/unselected/SKILL.md").write_text("ignored")
    monkeypatch.setenv("POWERSPEC_OPENSPEC_SOURCE", str(upstream))

    snapshot = prepare_snapshot(declaration(), tmp_path / "checkout", tmp_path / "stage")

    assert {path.name for path in (snapshot / "skills").iterdir() if path.is_dir()} == set(SKILLS)
    manifest = json.loads((snapshot / MANIFEST).read_text())
    assert manifest["revision"] == REVISION
    assert "skills/openspec-one/SKILL.md" in manifest["files"]
    assert (snapshot / "skills/UPSTREAM_LICENSE.txt").read_text() == "license\n"


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda value: value.pop("revision"), "missing"),
        (lambda value: value.__setitem__("revision", "main"), "full commit"),
        (lambda value: value.__setitem__("skills", ["../escape"]), "skill names"),
    ],
)
def test_invalid_declarations_fail_closed(tmp_path, monkeypatch, mutate, message):
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    source(upstream)
    monkeypatch.setenv("POWERSPEC_OPENSPEC_SOURCE", str(upstream))
    config = declaration()
    mutate(config)
    with pytest.raises(BuildSourceError, match=message):
        prepare_snapshot(config, tmp_path / "checkout", tmp_path / "stage")


def test_missing_or_mismatched_skill_root_fails_build(tmp_path, monkeypatch):
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    source(upstream)
    (upstream / "skills/openspec-two/SKILL.md").write_text(
        "---\nname: wrong-name\n---\n", encoding="utf-8"
    )
    monkeypatch.setenv("POWERSPEC_OPENSPEC_SOURCE", str(upstream))
    with pytest.raises(BuildSourceError, match="identity"):
        prepare_snapshot(declaration(), tmp_path / "checkout", tmp_path / "stage")

    (upstream / "skills/openspec-two").rename(upstream / "skills/missing")
    with pytest.raises(BuildSourceError, match="regular directory"):
        prepare_snapshot(declaration(), tmp_path / "checkout", tmp_path / "second-stage")


def test_redirected_content_cannot_escape_the_declared_skill(tmp_path, monkeypatch):
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    source(upstream)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside")
    link = upstream / "skills/openspec-one/escape.txt"
    try:
        link.symlink_to(outside)
    except OSError as error:
        pytest.skip(str(error))
    monkeypatch.setenv("POWERSPEC_OPENSPEC_SOURCE", str(upstream))
    with pytest.raises(BuildSourceError, match="redirected"):
        prepare_snapshot(declaration(), tmp_path / "checkout", tmp_path / "stage")


def test_carried_snapshot_rejects_content_changes_without_network(tmp_path, monkeypatch):
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    source(upstream)
    monkeypatch.setenv("POWERSPEC_OPENSPEC_SOURCE", str(upstream))
    carried = tmp_path / "checkout/powerspec_build/openspec"
    prepare_snapshot(declaration(), tmp_path / "first", carried)
    (carried / "skills/openspec-one/reference.md").write_text("changed")
    monkeypatch.delenv("POWERSPEC_OPENSPEC_SOURCE")
    with pytest.raises(BuildSourceError, match="manifest"):
        prepare_snapshot(declaration(), tmp_path / "checkout", tmp_path / "unused")

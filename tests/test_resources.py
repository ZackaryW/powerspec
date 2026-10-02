from pathlib import Path
from zipfile import ZipFile

import pytest

import powerspec.resources as resources
from powerspec.catalog import ConfigurationError


def test_builtin_catalog_contains_complete_skill_inputs():
    with resources.builtin_catalog_root() as root:
        skills = {path.parent.name for path in Path(root).glob("skills/*/SKILL.md")}
        assert "openspec-apply-change" in skills
        assert "openspec-verify-change" in skills
        assert "pspec-skill-bootstrap" in skills
        assert (root / "skills/pspec_tdd/pspec.toml").is_file()
        assert (root / "skills/pspec_tdd/languages/python.md").is_file()
        assert (root / "skills/UPSTREAM_LICENSE.txt").is_file()
        assert (root / "skills/UPSTREAM_PROVENANCE.md").is_file()


def test_missing_catalog_is_diagnosed_without_fetch_or_generation(tmp_path, monkeypatch):
    missing_package = tmp_path / "package"
    missing_checkout = tmp_path / "checkout"
    monkeypatch.setattr(resources, "files", lambda _name: missing_package)
    monkeypatch.setattr(resources, "_checkout_catalog_root", lambda: missing_checkout)

    with pytest.raises(ConfigurationError, match="builtin catalog is missing"):
        with resources.builtin_catalog_root():
            pass


def test_built_wheel_has_no_checkout_paths(tmp_path):
    wheels = list((Path(__file__).resolve().parents[1] / "dist").glob("powerspec-*.whl"))
    if not wheels:
        pytest.skip("distribution wheel has not been built")
    with ZipFile(wheels[0]) as archive:
        names = archive.namelist()
    assert "powerspec/_resources/catalog/profiles/builtin.toml" in names
    assert "powerspec/_resources/catalog/skills/pspec_tdd/languages/python.md" in names
    assert not any(".cache" in name or "Documents/GitHub" in name for name in names)

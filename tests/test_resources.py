from pathlib import Path
import tomllib
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
        assert "pspec-workset" in skills
        assert "pspec-repo-investigation" in skills
        assert (root / "profiles/repository-investigation.toml").is_file()
        assert (root / "traits/repository-investigation.toml").is_file()
        assert (root / "contexts/archive-temporary-state.toml").is_file()
        assert (root / "skills/pspec-tdd/pspec.toml").is_file()
        assert (root / "skills/pspec-tdd/languages/python.md").is_file()
        assert (root / "skills/UPSTREAM_LICENSE.txt").is_file()
        assert (root / "skills/UPSTREAM_PROVENANCE.md").is_file()


def test_builtin_guidance_uses_canonical_cli_surface():
    with resources.builtin_catalog_root() as root:
        bootstrap = (root / "skills/pspec-skill-bootstrap/SKILL.md").read_text(encoding="utf-8")
        trait = (root / "traits/skill-bootstrap.toml").read_text(encoding="utf-8")
        archive = (root / "contexts/archive-temporary-state.toml").read_text(encoding="utf-8")
    assert "pspec resolve skill" in bootstrap and "pspec init --agent" in bootstrap
    assert tomllib.loads(trait)["body"] == ""
    assert "pspec state clear --change" in archive
    assert "pspec install --agent" not in bootstrap


def test_missing_catalog_is_diagnosed_without_fetch_or_generation(tmp_path, monkeypatch):
    missing_package = tmp_path / "package"
    missing_checkout = tmp_path / "checkout"
    monkeypatch.setattr(resources, "files", lambda _name: missing_package)
    monkeypatch.setattr(resources, "_distribution_catalog_root", lambda: None)
    monkeypatch.setattr(resources, "_checkout_catalog_root", lambda: missing_checkout)

    with pytest.raises(ConfigurationError, match="builtin catalog is missing"):
        with resources.builtin_catalog_root():
            pass


def test_editable_catalog_overlays_live_authored_files_on_packaged_upstream(tmp_path, monkeypatch):
    checkout = tmp_path / "checkout"
    installed = tmp_path / "installed"
    (checkout / "profiles").mkdir(parents=True)
    (installed / "profiles").mkdir(parents=True)
    (installed / "skills/openspec-example").mkdir(parents=True)
    (installed / "profiles/live.toml").write_text('scope="stale"')
    (checkout / "profiles/live.toml").write_text('scope="user"')
    (installed / "skills/openspec-example/SKILL.md").write_text("upstream")
    monkeypatch.setattr(resources, "files", lambda _name: tmp_path / "missing")
    monkeypatch.setattr(resources, "_checkout_catalog_root", lambda: checkout)
    monkeypatch.setattr(resources, "_distribution_catalog_root", lambda: installed)

    with resources.builtin_catalog_root() as root:
        assert (root / "profiles/live.toml").read_text() == 'scope="user"'
        assert (root / "skills/openspec-example/SKILL.md").read_text() == "upstream"


def test_built_wheel_has_no_checkout_paths(tmp_path):
    project = Path(__file__).resolve().parents[1]
    version = tomllib.loads((project / "pyproject.toml").read_text())["project"]["version"]
    wheels = list((project / "dist").glob(f"powerspec-{version}-*.whl"))
    if not wheels:
        pytest.skip("distribution wheel has not been built")
    with ZipFile(wheels[0]) as archive:
        names = archive.namelist()
        prefix = 'powerspec/_resources/catalog/'
        assert tomllib.loads(archive.read(prefix + 'traits/skill-bootstrap.toml').decode())['body'] == ''
        assert '@builtin/skill-bootstrap' not in tomllib.loads(archive.read(prefix + 'profiles/builtin.toml').decode())['traits']
        for skill in ('pspec-skill-bootstrap', 'pspec-tdd', 'pspec-smarter-decision'):
            assert 'resolve skill --path' in archive.read(prefix + f'skills/{skill}/SKILL.md').decode()
    assert "powerspec/_resources/catalog/profiles/builtin.toml" in names
    assert "powerspec/_resources/catalog/skills/pspec-repo-investigation/SKILL.md" in names
    assert "powerspec/_resources/catalog/contexts/archive-temporary-state.toml" in names
    assert "powerspec/_resources/catalog/skills/pspec-tdd/languages/python.md" in names
    assert not any(".cache" in name or "Documents/GitHub" in name for name in names)

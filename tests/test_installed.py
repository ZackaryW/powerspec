from pathlib import Path

import pytest

from powerspec.catalog import ConfigurationError
from powerspec.installed import installed_skill


def put_skill(root: Path, name: str):
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Example.\n---\n\n# Example\n",
        encoding="utf-8",
    )
    return skill


def snapshot(root: Path):
    return {
        path.relative_to(root).as_posix(): path.read_bytes() if path.is_file() else None
        for path in root.rglob("*")
    }


def test_explicit_agent_lookup_is_read_only_and_reports_missing(tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    found = put_skill(home / ".codex/skills", "example")
    before = snapshot(tmp_path)
    located = installed_skill("codex", "example", cwd=project, home=home)
    assert located.root == found.resolve() and located.scope == "user"
    with pytest.raises(ConfigurationError, match="missing.*codex"):
        installed_skill("codex", "absent", cwd=project, home=home)
    assert snapshot(tmp_path) == before


def test_codex_coexistence_requires_validated_host_selection(tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    user = put_skill(home / ".codex/skills", "example")
    local = put_skill(project / ".agents/skills", "example")
    stray = put_skill(tmp_path / "stray", "example")
    before = snapshot(tmp_path)
    with pytest.raises(ConfigurationError, match="unresolved"):
        installed_skill("codex", "example", cwd=project, home=home)
    chosen = installed_skill("codex", "example", cwd=project, home=home, selected=local)
    assert chosen.root == local.resolve() and chosen.provenance == "caller-evidence"
    with pytest.raises(ConfigurationError, match="invalid"):
        installed_skill("codex", "example", cwd=project, home=home, selected=stray)
    assert user.exists() and snapshot(tmp_path) == before


def test_unsupported_agent_does_not_fall_back_to_another_agent(tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    put_skill(home / ".codex/skills", "example")
    before = snapshot(tmp_path)
    with pytest.raises(ConfigurationError, match="unsupported"):
        installed_skill("unknown", "example", cwd=project, home=home)
    assert snapshot(tmp_path) == before

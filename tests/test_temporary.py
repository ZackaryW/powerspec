from pathlib import Path
import subprocess

import pytest

from powerspec.catalog import ConfigurationError
from powerspec.temporary import flush_current


def put(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def project(tmp_path, current=None):
    root = tmp_path / "project"
    root.mkdir(parents=True)
    subprocess.run(["git", "init", "--quiet", str(root)], check=True)
    put(root, "openspec/.pspec/config.toml", '[vars]\npersistent = "keep"\n')
    put(root, "openspec/config.yaml", "schema: spec-driven\n")
    if current is not None:
        put(root, "openspec/.pspec/current.toml", current)
    return root


def test_full_flush_is_idempotent_and_does_not_create_missing_state(tmp_path):
    root = project(tmp_path)
    current = root / "openspec/.pspec/current.toml"
    missing = flush_current(root)
    assert not missing.updated and missing.path == current
    assert not current.exists()

    current.write_text("# keep while empty\n[vars]\n", encoding="utf-8")
    before = current.read_bytes()
    empty = flush_current(root)
    assert not empty.updated and current.read_bytes() == before


def test_full_flush_resets_all_temporal_values_only(tmp_path):
    root = project(tmp_path, '''
[vars]
shared = "temporary"
[_change.one]
answer = true
[_change.two]
count = 2
''')
    config = root / "openspec/.pspec/config.toml"
    yaml = root / "openspec/config.yaml"
    config_before, yaml_before = config.read_bytes(), yaml.read_bytes()
    result = flush_current(root / "openspec")
    assert result.updated
    assert result.path.read_text(encoding="utf-8") == "[vars]\n"
    assert config.read_bytes() == config_before and yaml.read_bytes() == yaml_before


def test_change_flush_preserves_shared_other_changes_and_comments(tmp_path):
    original = '''# temporal answers
[vars] # shared comment
language = "python" # inline

[_change.one]
mode = "remove"

[_change.two] # retain table
mode = "keep" # retain value
'''
    root = project(tmp_path, original)
    result = flush_current(root, change="one")
    rendered = result.path.read_text(encoding="utf-8")
    assert result.updated
    assert "_change.one" not in rendered and 'mode = "remove"' not in rendered
    assert "# temporal answers" in rendered and "# shared comment" in rendered
    assert "_change.two" in rendered and "# retain value" in rendered
    assert 'language = "python"' in rendered


def test_change_flush_supports_quoted_dotted_name_and_removes_empty_container(tmp_path):
    root = project(tmp_path, '''
[vars]
shared = true
[_change."release.v1"]
answer = "temporary"
''')
    result = flush_current(root, change="release.v1")
    rendered = result.path.read_text(encoding="utf-8")
    assert result.updated and "_change" not in rendered
    assert "shared = true" in rendered


def test_absent_change_is_exact_byte_unchanged_and_empty_name_is_rejected(tmp_path):
    root = project(tmp_path, '[vars]\nshared = "value"\n')
    current = root / "openspec/.pspec/current.toml"
    before = current.read_bytes()
    result = flush_current(root, change="missing")
    assert not result.updated and current.read_bytes() == before
    with pytest.raises(ConfigurationError, match="nonempty"):
        flush_current(root, change="  ")
    assert current.read_bytes() == before


@pytest.mark.parametrize("current", ["invalid = [", 'profile = "not-temporal"\n'])
def test_malformed_or_unsupported_current_is_preserved(tmp_path, current):
    root = project(tmp_path, current)
    path = root / "openspec/.pspec/current.toml"
    before = path.read_bytes()
    with pytest.raises(ConfigurationError, match="invalid temporal state"):
        flush_current(root)
    assert path.read_bytes() == before


def test_publication_failure_preserves_original_and_cleans_staging(tmp_path, monkeypatch):
    import powerspec.temporary as temporary

    root = project(tmp_path, '[vars]\nanswer = "temporary"\n')
    path = root / "openspec/.pspec/current.toml"
    before = path.read_bytes()

    def fail(_source, _destination):
        raise OSError("injected replacement failure")

    monkeypatch.setattr(temporary.os, "replace", fail)
    with pytest.raises(ConfigurationError, match="publication failed"):
        flush_current(root)
    assert path.read_bytes() == before
    assert not list(path.parent.glob(".current.toml.pspec-*"))


def test_worktree_uses_its_own_consumer(tmp_path):
    root = project(tmp_path, '[vars]\nroot = "keep"\n')
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "commit", "--allow-empty", "-qm", "initial"], cwd=root, check=True)
    worktree = tmp_path / "worktree"
    subprocess.run(["git", "worktree", "add", "--detach", str(worktree)],
                   cwd=root, check=True, capture_output=True)
    put(worktree, "openspec/.pspec/config.toml", "[vars]\n")
    current = put(worktree, "openspec/.pspec/current.toml", '[vars]\nworktree = "clear"\n')
    assert flush_current(worktree / "openspec").updated
    assert current.read_text(encoding="utf-8") == "[vars]\n"
    assert (root / "openspec/.pspec/current.toml").read_text(encoding="utf-8").endswith(
        'root = "keep"\n')


def test_cli_reports_updated_unchanged_and_no_consumer(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from powerspec.cli import app

    root = project(tmp_path, '[_change.work]\nanswer = "temporary"\n')
    monkeypatch.chdir(root / "openspec")
    updated = CliRunner().invoke(app, ["flush", "--change", "work"])
    unchanged = CliRunner().invoke(app, ["flush", "--change", "work"])
    assert updated.exit_code == unchanged.exit_code == 0
    assert updated.stdout.startswith("updated:")
    assert unchanged.stdout.startswith("unchanged:")

    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)
    missing = CliRunner().invoke(app, ["flush"])
    assert missing.exit_code == 1 and missing.stdout == ""
    assert "no owning" in missing.stderr.lower()

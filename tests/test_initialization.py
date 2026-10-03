import subprocess
from pathlib import Path

import pytest

from powerspec.catalog import Catalog, ConfigurationError


def setup_repo(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    subprocess.run(["git", "init", "--quiet", str(project)], check=True)
    catalog = tmp_path / "catalog"
    (catalog / "profiles").mkdir(parents=True)
    (catalog / "profiles/base.toml").write_text('scope="user"\n')
    consumer = project / "openspec/.pspec"
    consumer.mkdir(parents=True)
    (consumer / "config.toml").write_text('profile="@builtin/base"\n[vars]\nlanguage="python"\n')
    return project, Catalog(builtin=catalog)


def bootstrap(root):
    (root / "openspec").mkdir(exist_ok=True)
    (root / "openspec/config.yaml").write_text("schema: spec-driven\n")


def test_init_uses_git_root_and_preserves_persistent_and_temporal_files(tmp_path, monkeypatch):
    import powerspec.initialization as m
    project, catalog = setup_repo(tmp_path)
    nested = project / "src/package"
    nested.mkdir(parents=True)
    state = project / "openspec/.pspec"
    config_before = (state / "config.toml").read_bytes()
    (state / "current.toml").write_text('[_change.work]\nanswer=true\n')
    (state / ".gitignore").write_text("cache/\n")
    current_before = (state / "current.toml").read_bytes()
    native = project / ".agents/skills/foreign/SKILL.md"
    native.parent.mkdir(parents=True)
    native.write_text("preserved")
    monkeypatch.setattr(m, "bootstrap_openspec", bootstrap)
    plan = m.plan_initialization(nested)
    assert plan.root == project.resolve()
    result = m.initialize(plan)
    assert (state / "config.toml").read_bytes() == config_before
    assert (state / "current.toml").read_bytes() == current_before
    assert native.read_text() == "preserved"
    assert (state / ".gitignore").read_text() == "cache/\n/current.toml\n"
    assert subprocess.run(["git", "check-ignore", "openspec/.pspec/current.toml"], cwd=project).returncode == 0
    assert subprocess.run(["git", "check-ignore", "openspec/.pspec/config.toml"], cwd=project).returncode == 1
    first_yaml = (project / "openspec/config.yaml").read_bytes()
    monkeypatch.setattr(m, "bootstrap_openspec", lambda _: pytest.fail("already bootstrapped"))
    assert m.initialize(plan).root == project.resolve()
    assert (project / "openspec/config.yaml").read_bytes() == first_yaml


def test_missing_selection_uses_globals_without_requiring_agent_or_catalog(tmp_path):
    from powerspec.initialization import plan_initialization
    project, catalog = setup_repo(tmp_path)
    (project / "openspec/.pspec/config.toml").unlink()
    plan = plan_initialization(project)
    assert plan.profile is None
    assert not (project / "openspec/config.yaml").exists()


def test_tracked_current_is_reported_without_untracking(tmp_path, monkeypatch):
    import powerspec.initialization as m
    project, catalog = setup_repo(tmp_path)
    current = project / "openspec/.pspec/current.toml"
    current.write_text("[vars]\n")
    subprocess.run(["git", "add", "openspec/.pspec/current.toml"], cwd=project, check=True)
    monkeypatch.setattr(m, "bootstrap_openspec", bootstrap)
    result = m.initialize(m.plan_initialization(project))
    assert any("tracked" in warning for warning in result.warnings)
    assert subprocess.run(["git", "ls-files", "--error-unmatch", "openspec/.pspec/current.toml"], cwd=project).returncode == 0


def test_worktree_git_file_is_boundary(tmp_path, monkeypatch):
    import powerspec.initialization as m
    project, catalog = setup_repo(tmp_path)
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "commit", "--allow-empty", "-qm", "initial"], cwd=project, check=True)
    worktree = tmp_path / "worktree"
    subprocess.run(["git", "worktree", "add", "--detach", str(worktree)], cwd=project, check=True, capture_output=True)
    state = worktree / "openspec/.pspec"
    state.mkdir(parents=True)
    (state / "config.toml").write_text('profile="@builtin/base"\n')
    monkeypatch.setattr(m, "bootstrap_openspec", bootstrap)
    plan = m.plan_initialization(state)
    assert plan.root == worktree.resolve()
    m.initialize(plan)
    assert (worktree / "openspec/config.yaml").is_file()
    assert not (project / "openspec/config.yaml").exists()


def test_bootstrap_failure_keeps_consumer_values(tmp_path, monkeypatch):
    import powerspec.initialization as m
    project, catalog = setup_repo(tmp_path)
    before = (project / "openspec/.pspec/config.toml").read_bytes()
    def fail(root):
        raise ConfigurationError("OpenSpec failed")
    monkeypatch.setattr(m, "bootstrap_openspec", fail)
    with pytest.raises(ConfigurationError, match="OpenSpec failed"):
        m.initialize(m.plan_initialization(project))
    assert (project / "openspec/.pspec/config.toml").read_bytes() == before


def test_new_profile_selector_is_persisted_without_overwriting_existing_selection(tmp_path, monkeypatch):
    import powerspec.initialization as m
    project, catalog = setup_repo(tmp_path)
    path = project / "openspec/.pspec/config.toml"
    path.unlink()
    monkeypatch.setattr(m, "bootstrap_openspec", bootstrap)
    plan = m.plan_initialization(project, profile="@builtin/base")
    m.initialize(plan)
    assert 'profile = "@builtin/base"' in path.read_text()
    with pytest.raises(ConfigurationError, match="already selects"):
        m.plan_initialization(project, profile="@builtin/other")


def test_changed_configuration_aborts_before_bootstrap(tmp_path, monkeypatch):
    import powerspec.initialization as m
    project, catalog = setup_repo(tmp_path)
    plan = m.plan_initialization(project)
    plan.config_path.write_text('profile="@builtin/base"\n[vars]\nnew=true\n')
    monkeypatch.setattr(m, "bootstrap_openspec", lambda _: pytest.fail("must preserve edit"))
    with pytest.raises(ConfigurationError, match="changed after"):
        m.initialize(plan)


def test_bootstrap_invokes_upstream_with_no_local_tools(tmp_path, monkeypatch):
    import powerspec.initialization as m
    calls = []
    monkeypatch.setattr(m.shutil, "which", lambda _: "openspec")
    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        if "--version" in argv:
            return subprocess.CompletedProcess(argv, 0, "1.13.2", "")
        bootstrap(tmp_path)
        return subprocess.CompletedProcess(argv, 0, "initialized", "")
    monkeypatch.setattr(m.subprocess, "run", run)
    m.bootstrap_openspec(tmp_path)
    assert calls[-1][0] == ["openspec", "init", str(tmp_path), "--tools", "none", "--no-animation"]
    assert calls[-1][1]["stdin"] == subprocess.DEVNULL


def test_init_cli_reports_availability_and_reuses_configuration(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from powerspec.cli import app
    import powerspec.initialization as m
    project, _ = setup_repo(tmp_path)
    monkeypatch.setattr(m, "bootstrap_openspec", bootstrap)
    monkeypatch.chdir(project)
    result = CliRunner().invoke(app, ["init"])
    assert result.exit_code == 0, result.output
    assert "initialized:" in result.stdout
    assert "Run pspec sync" in result.stdout
    assert "pspec install --agent" in result.stdout
    assert not (project / ".agents").exists()


@pytest.mark.parametrize("content", [None, '[vars]\nkeep=true\n', 'profile=""\n[vars]\nkeep=true\n'])
def test_empty_profile_initializes_global_bundle(tmp_path, monkeypatch, content):
    import powerspec.initialization as m
    project, _ = setup_repo(tmp_path)
    catalog_root = tmp_path / "catalog"
    (catalog_root / "profiles/global.toml").write_text('global=true\n[vars]\nmode="global"\n')
    config = project / "openspec/.pspec/config.toml"
    if content is None:
        config.unlink()
    else:
        config.write_text(content)
    monkeypatch.setattr(m, "bootstrap_openspec", bootstrap)
    plan = m.plan_initialization(project)
    assert plan.profile is None
    result = m.initialize(plan)
    assert config.read_text() == (content if content is not None else "[vars]\n")


def test_init_does_not_provision_global_or_selected_skill_scopes(tmp_path, monkeypatch):
    import powerspec.initialization as m
    from test_provisioning import bundle
    bundle(tmp_path)
    project = tmp_path / "project"
    subprocess.run(["git", "init", "--quiet", str(project)], check=True)
    global_profile = tmp_path / "catalog/profiles/shared.toml"
    global_profile.write_text('global=true\n' + global_profile.read_text())
    monkeypatch.setattr(m, "bootstrap_openspec", bootstrap)
    plan = m.plan_initialization(project, profile="@builtin/local")
    result = m.initialize(plan)
    assert result.root == project.resolve()
    assert not (tmp_path / "home/.codex/skills").exists()
    assert not (project / ".agents/skills").exists()


def test_current_ignore_rule_overrides_earlier_negation(tmp_path, monkeypatch):
    import powerspec.initialization as m
    project, catalog = setup_repo(tmp_path)
    ignore = project / "openspec/.pspec/.gitignore"
    ignore.write_text('/current.toml\n!current.toml\n')
    monkeypatch.setattr(m, "bootstrap_openspec", bootstrap)
    m.initialize(m.plan_initialization(project))
    assert ignore.read_text().startswith('/current.toml\n!current.toml\n')
    assert subprocess.run(["git", "check-ignore", "openspec/.pspec/current.toml"], cwd=project).returncode == 0

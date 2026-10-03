import json
import subprocess
from contextlib import contextmanager
from pathlib import Path

from typer.testing import CliRunner

from powerspec.catalog import Catalog
from powerspec.hooks import dispatch
from powerspec.profiles import compose
from powerspec.provisioning import plan_skills, provision_skills
from powerspec.resources import builtin_catalog_root


def put(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def consumer(tmp_path, *, excluded=()):
    project = tmp_path / "project"
    project.mkdir(parents=True)
    subprocess.run(["git", "init", "--quiet", str(project)], check=True)
    excludes = json.dumps(list(excluded))
    put(project, "openspec/.pspec/config.toml",
        f'profile = "@builtin/python-simple-cli"\nexclude-profiles = {excludes}\n\n'
        '[vars]\nutility_path = "src/powerspec/utils"\n')
    return project


def payload(project, source="startup"):
    return {"session_id": "test", "cwd": str(project.resolve()),
            "hook_event_name": "SessionStart", "source": source}


def test_global_bundle_composes_once_and_excludes_only_its_contributions():
    excluded = ["@builtin/zmem-lifecycle", "@builtin/adhd-friendly"]
    with builtin_catalog_root() as root:
        catalog = Catalog(builtin=root)
        selected = compose(catalog, "@builtin/python-simple-cli", agent="codex",
                           exclude_profiles=excluded)
        assert [item.ref for item in selected.profiles].count(
            "@builtin/repository-investigation") == 1
        assert [item.resource.name for item in selected.skills].count(
            "pspec-repo-investigation") == 1
        assert [item.ref for item in selected.traits].count(
            "@builtin/repository-investigation") == 1
        assert {item.name for item in selected.contexts} == {
            "archive-temporary-state", "python-simple-cli", "utility-plan", "utility-apply",
        }
        assert "pspec-bdd" not in {item.resource.name for item in selected.skills}

        without = compose(
            catalog, "@builtin/python-simple-cli", agent="codex",
            exclude_profiles=[*excluded, "@builtin/repository-investigation"],
        )
        assert not without.armed("profile", "@builtin/repository-investigation")
        assert not without.armed("trait", "@builtin/repository-investigation")
        assert not without.armed("skill", "@builtin/pspec-repo-investigation")
        assert without.armed("skill", "@builtin/pspec-skill-bootstrap")
        assert without.armed("skill", "@builtin/pspec-smarter-decision")


def test_standalone_trait_is_omitted_when_its_skill_is_not_armed(tmp_path):
    root = tmp_path / "catalog"
    put(root, "profiles/standalone.toml",
        'traits = ["@builtin/repository-investigation"]\n')
    put(root, "traits/repository-investigation.toml", '''
hooks = ["sessionStart", "afterCompaction"]
when = "armed('skill', '@builtin/pspec-repo-investigation')"
body = "must not appear"
''')
    project = tmp_path / "project"
    project.mkdir()
    subprocess.run(["git", "init", "--quiet", str(project)], check=True)
    put(project, "openspec/.pspec/config.toml",
        'profile = "@builtin/standalone"\n')
    assert dispatch(logical_event="sessionStart", agent="codex",
                    payload=payload(project), catalog=Catalog(builtin=root)) is None


def test_generic_hooks_deliver_reminder_without_starting_other_workflows(tmp_path):
    excluded = ["@builtin/zmem-lifecycle", "@builtin/adhd-friendly"]
    project = consumer(tmp_path, excluded=excluded)
    config_yaml = put(project, "openspec/config.yaml", "schema: spec-driven\n")
    original = config_yaml.read_bytes()
    with builtin_catalog_root() as root:
        catalog = Catalog(builtin=root)
        start = dispatch(logical_event="sessionStart", agent="codex",
                         payload=payload(project), catalog=catalog)
        compact = dispatch(logical_event="afterCompaction", agent="codex",
                           payload=payload(project, "compact"), catalog=catalog)
    for guidance in (start, compact):
        assert guidance is not None
        assert "pspec-repo-investigation" in guidance
        assert "pspec-skill-bootstrap" in guidance
        assert "pspec-smarter-decision" in guidance
        assert "does not start an investigation" in guidance
        assert "Which language" not in guidance
        assert "bdd_framework" not in guidance
    assert config_yaml.read_bytes() == original


def test_exclusion_changes_runtime_selection_without_removing_registration(tmp_path):
    project = consumer(tmp_path, excluded=[
        "@builtin/zmem-lifecycle", "@builtin/adhd-friendly",
        "@builtin/repository-investigation",
    ])
    with builtin_catalog_root() as root:
        guidance = dispatch(logical_event="afterCompaction", agent="claude",
                            payload=payload(project, "compact"),
                            catalog=Catalog(builtin=root))
    assert guidance is not None
    assert "pspec-repo-investigation" not in guidance
    assert "pspec-skill-bootstrap" in guidance
    assert "pspec-smarter-decision" in guidance


def test_investigation_skill_is_provisioned_as_an_ordinary_skill(tmp_path, monkeypatch):
    from powerspec.cli import app
    import powerspec.cli.skill as cli

    project = consumer(tmp_path, excluded=[
        "@builtin/zmem-lifecycle", "@builtin/adhd-friendly",
    ])
    home, registry = tmp_path / "home", tmp_path / "registry"
    with builtin_catalog_root() as root:
        catalog = Catalog(builtin=root)
        bundle = compose(catalog, "@builtin/python-simple-cli", agent="codex",
                         project_root=project,
                         exclude_profiles=["@builtin/zmem-lifecycle",
                                           "@builtin/adhd-friendly"])
        plan = tuple(item for item in plan_skills(bundle)
                     if item.name == "pspec-repo-investigation")
        assert len(plan) == 1 and plan[0].scope == "user"
        result = provision_skills(plan, home=home, registry=registry)
        catalog_root = Path(root)
    assert result.ok

    @contextmanager
    def resources():
        yield catalog_root

    monkeypatch.setattr(cli, "builtin_catalog_root", resources)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("CODEX_HOME", str(home / ".codex"))
    monkeypatch.chdir(project)
    resolved = CliRunner().invoke(
        app, ["resolve", "skill", "pspec-repo-investigation", "--agent", "codex"],
    )
    assert resolved.exit_code == 0, resolved.output
    assert resolved.stdout.strip() == "null"

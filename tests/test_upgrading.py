from pathlib import Path
from types import SimpleNamespace

import pytest

from powerspec.catalog import Catalog, ConfigurationError
from powerspec.models import ConsumerConfig
from powerspec.profiles import compose
from powerspec.provisioning import HookOutcome, ProvisionResult, SkillOutcome, plan_skills, provision_skills
from powerspec.sources import SourceBinding
from powerspec.upgrading import upgrade_consumer


def put(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def skill(root: Path, folder: str, name: str, body: str):
    put(root / f"skills/{folder}/SKILL.md",
        f"---\nname: {name}\ndescription: Test.\n---\n\n{body}\n")
    put(root / f"skills/{folder}/references/detail.md", f"detail: {body}")


def binding(root: Path, revision: str):
    return SourceBinding("tools", "https://example.test/tools", "main", revision,
                         "1" * 64, "artifact-" + revision[0], root)


class Store:
    def __init__(self, old, new=None, failure=None):
        self.old = old
        self.new = new
        self.failure = failure
        self.calls = []

    def lookup(self, identity, recipe):
        self.calls.append(("lookup", identity, recipe))
        if self.failure == "lookup":
            raise ConfigurationError("source registration is unavailable")
        return self.old

    def acquire(self, identity, recipe):
        self.calls.append(("acquire", identity, recipe))
        if self.failure == "acquire":
            raise ConfigurationError("controlled acquisition failure")
        return self.new


def fixture(tmp_path, *, empty=False, malformed=False):
    builtin = tmp_path / "catalog"
    old = tmp_path / "old"
    new = tmp_path / "new"
    project = tmp_path / "project"
    home = tmp_path / "home"
    registry = tmp_path / "registry"
    project.mkdir()
    put(builtin / "profiles/main.toml",
        'scope="user"\nskills=["@builtin/helper","tools/skills/*"]\n'
        '[[source]]\nid="tools"\nprovider="git"\n'
        'origin="https://example.test/tools"\nreference="main"\n')
    skill(builtin, "helper", "helper", "bundled helper")
    skill(old, "a-folder", "a", "old a")
    skill(old, "b-folder", "b", "old b")
    (new / "skills").mkdir(parents=True)
    if not empty:
        skill(new, "renamed-a", "a", "new a")
    if malformed:
        put(new / "skills/bad/SKILL.md", "missing frontmatter")
    consumer = SimpleNamespace(
        config=ConsumerConfig(profile="@builtin/main"),
        git_root=project,
    )
    old_binding, new_binding = binding(old, "a" * 40), binding(new, "b" * 40)
    bundle = compose(Catalog(builtin=builtin, gitsources={"tools": old_binding}),
                     "@builtin/main", agent="codex", project_root=project)
    installed = provision_skills(plan_skills(bundle), home=home, registry=registry)
    assert installed.ok
    return SimpleNamespace(
        builtin=builtin, old=old_binding, new=new_binding, consumer=consumer,
        home=home, registry=registry,
    )


def run_upgrade(data, **overrides):
    return upgrade_consumer(
        builtin=data.builtin,
        consumer=data.consumer,
        agent="codex",
        source_store=overrides.pop("source_store", Store(data.old, data.new)),
        home=data.home,
        registry=data.registry,
        **overrides,
    )


def test_upgrade_refreshes_updates_and_removes_confirmed_obsolete_skill(tmp_path):
    data = fixture(tmp_path)
    result = run_upgrade(data)
    assert result.ok, result.diagnostics
    assert [item.name for item in result.removed] == ["b"]
    assert (data.home / ".codex/skills/a/SKILL.md").read_text().endswith("new a\n")
    assert (data.home / ".codex/skills/a/references/detail.md").read_text() == "detail: new a"
    assert not (data.home / ".codex/skills/b").exists()


def test_upgrade_replaces_owned_bootstrap_guidance_preserving_foreign_assets(tmp_path):
    from powerspec.resources import builtin_catalog_root
    data = fixture(tmp_path)
    # Install the old helper as owned content before supplying the new resource.
    skill(data.builtin, 'pspec-skill-bootstrap', 'pspec-skill-bootstrap',
          'Before using another skill, resolve it by name through Powerspec.')
    profile = data.builtin / 'profiles/main.toml'
    profile.write_text(profile.read_text().replace('"@builtin/helper",', '"@builtin/helper","@builtin/pspec-skill-bootstrap",'))
    old = compose(Catalog(builtin=data.builtin, gitsources={'tools': data.old}),
                  '@builtin/main', agent='codex', project_root=data.consumer.git_root)
    assert provision_skills(plan_skills(old), home=data.home, registry=data.registry).ok
    foreign = put(data.home / '.codex/skills/foreign/SKILL.md', 'User-owned instructions')
    with builtin_catalog_root() as root:
        revised = (root / 'skills/pspec-skill-bootstrap/SKILL.md').read_text()
    put(data.builtin / 'skills/pspec-skill-bootstrap/SKILL.md', revised)
    result = run_upgrade(data)
    assert result.ok, result.diagnostics
    installed = data.home / '.codex/skills/pspec-skill-bootstrap/SKILL.md'
    assert installed.read_text() == revised
    assert '--path' in installed.read_text()
    assert 'Before using another skill' not in installed.read_text()
    assert foreign.read_text() == 'User-owned instructions'


def test_successful_empty_refresh_removes_last_wildcard_matches(tmp_path):
    data = fixture(tmp_path, empty=True)
    result = run_upgrade(data)
    assert result.ok and {item.name for item in result.removed} == {"a", "b"}
    assert not (data.home / ".codex/skills/a").exists()
    assert not (data.home / ".codex/skills/b").exists()


@pytest.mark.parametrize("failure", ["lookup", "acquire"])
def test_unavailable_or_removed_registration_preserves_installed_copies(tmp_path, failure):
    data = fixture(tmp_path)
    result = run_upgrade(data, source_store=Store(data.old, data.new, failure))
    assert not result.ok and result.removed == ()
    assert (data.home / ".codex/skills/a").is_dir()
    assert (data.home / ".codex/skills/b").is_dir()


def test_malformed_replacement_preserves_installed_copies(tmp_path):
    data = fixture(tmp_path, malformed=True)
    result = run_upgrade(data)
    assert not result.ok and "frontmatter" in " ".join(result.diagnostics)
    assert (data.home / ".codex/skills/b").is_dir()


def test_late_provisioning_failure_does_not_start_obsolete_removal(tmp_path):
    data = fixture(tmp_path)

    def fail(plans, **_context):
        plan = plans[0]
        return ProvisionResult((SkillOutcome(plan.ref, "failed", plan, ("controlled late failure",)),))

    result = run_upgrade(data, provision=fail)
    assert not result.ok and result.removed == ()
    assert (data.home / ".codex/skills/b").is_dir()


def test_upgrade_passes_explicit_force_only_to_selected_skill_provisioning(tmp_path):
    data = fixture(tmp_path)
    seen = []

    def provision(plans, **context):
        seen.append(context["force"])
        return provision_skills(plans, **context)

    result = run_upgrade(data, force=True, provision=provision)

    assert result.ok and seen == [True]


def test_hook_failure_preserves_obsolete_skills_after_full_skill_reconciliation(tmp_path):
    data = fixture(tmp_path)
    seen = []

    def provision(plans, **context):
        seen.extend(plan.name for plan in plans)
        return provision_skills(plans, **context)

    failed = HookOutcome("codex", "failed", ("controlled hook failure",))
    result = run_upgrade(data, provision=provision, reconcile_hooks=lambda *a, **kw: failed)
    assert not result.ok and result.hooks == failed
    assert set(seen) == {"helper", "a"}
    assert result.removed == () and (data.home / ".codex/skills/b").is_dir()


def test_removal_finalization_failure_restores_complete_before_state(tmp_path):
    data = fixture(tmp_path)

    def fail_finalization(_plans, **_context):
        raise ConfigurationError("controlled finalization failure")

    result = run_upgrade(data, finalize=fail_finalization)
    assert result.status == "failed"
    assert "restored" in " ".join(result.diagnostics)
    assert (data.home / ".codex/skills/b/SKILL.md").is_file()


def test_no_remote_selection_is_a_successful_noop(tmp_path):
    builtin = tmp_path / "catalog"
    project = tmp_path / "project"
    project.mkdir()
    put(builtin / "profiles/main.toml", 'scope="user"\n')
    consumer = SimpleNamespace(config=ConsumerConfig(profile="@builtin/main"), git_root=project)
    store = Store(None, None)
    result = upgrade_consumer(
        builtin=builtin, consumer=consumer, agent="codex", source_store=store,
        home=tmp_path / "home", registry=tmp_path / "registry",
    )
    assert result.ok and store.calls == []

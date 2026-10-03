import json
from pathlib import Path
import pytest
from powerspec.catalog import Catalog, ConfigurationError
from powerspec.profiles import compose
from powerspec.sources import SourceBinding


def profile(root, name, **values):
    path = root / "profiles" / (name + ".toml")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    variables = values.pop("vars", {})
    for key, value in values.items():
        lines.append(f"{key} = {json.dumps(value)}")
    lines.append("[vars]")
    lines.extend(f"{key} = {json.dumps(value)}" for key,value in variables.items())
    path.write_text("\n".join(lines))


def skill(root, folder, name):
    path = root / "skills" / folder / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nname: {name}\n---\n")


def test_global_nested_scope_and_tiers(tmp_path):
    skill(tmp_path, "sk", "test-skill")
    profile(tmp_path, "global", **{"global": True}, profiles=["@builtin/shared"], vars={"mode": "global"})
    profile(tmp_path, "root", scope="project", profiles=["@builtin/shared", "@builtin/other"], skills=["@builtin/test-skill"], vars={"mode":"selected"})
    profile(tmp_path, "other", profiles=["@builtin/shared"])
    profile(tmp_path, "shared", skills=["@builtin/test-skill"], vars={"language":"python"})
    bundle = compose(Catalog(builtin=tmp_path), "@builtin/root", agent="codex", project_root=tmp_path)
    assert len(bundle.profiles) == 4
    assert bundle.selected_defaults == {"language":"python", "mode":"selected"}
    assert bundle.global_defaults == {"mode":"global"}
    assert {target.scope for target in bundle.skills} == {"user", "project"}
    assert len(bundle.skills) == 2
    assert all(t.agent == "codex" for t in bundle.skills)
    assert next(t for t in bundle.skills if t.scope == "project").project_root == tmp_path.resolve()


def test_exclusions_keep_shared_descendants(tmp_path):
    profile(tmp_path, "root", profiles=["@builtin/a", "@builtin/b"], **{"exclude-profiles":["@builtin/a"]})
    profile(tmp_path, "a", profiles=["@builtin/c", "@builtin/alone"])
    profile(tmp_path, "b", profiles=["@builtin/c"], **{"exclude-profiles":["@builtin/c"]})
    profile(tmp_path, "c")
    profile(tmp_path, "alone", **{"global":True})
    catalog = Catalog(builtin=tmp_path)
    bundle = compose(catalog, "@builtin/root", agent="codex", exclude_profiles=["@builtin/alone"])
    assert {p.ref for p in bundle.profiles} == {"@builtin/root", "@builtin/b", "@builtin/c"}
    with pytest.raises(ConfigurationError, match="excluded"):
        compose(catalog, "@builtin/root", agent="codex", exclude_profiles=["@builtin/root"])


@pytest.mark.parametrize("case", ["conflict", "cycle", "missing"])
def test_invalid_graph_has_no_bundle(tmp_path, case):
    profile(tmp_path, "root", profiles=["@builtin/child"], vars={"mode":"one"})
    if case == "conflict":
        profile(tmp_path, "child", vars={"mode":"two"})
    elif case == "cycle":
        profile(tmp_path, "child", profiles=["@builtin/root"])
    with pytest.raises(ConfigurationError, match="conflict|cycle|missing"):
        compose(Catalog(builtin=tmp_path), "@builtin/root", agent="codex")


def test_selected_names_conflict_but_distinct_scopes_do_not(tmp_path):
    one, two = tmp_path / "one", tmp_path / "two"
    skill(one, "a", "same")
    skill(two, "b", "same")
    profile(one, "root", skills=["@builtin/same"])
    catalog = Catalog(builtin=one, sources={"other":two})
    assert len(compose(catalog,"@builtin/root",agent="codex").skills) == 1
    profile(one, "root", skills=["@builtin/same", "@other/same"])
    with pytest.raises(ConfigurationError, match="conflict"):
        compose(Catalog(builtin=one,sources={"other":two}),"@builtin/root",agent="codex")
    profile(one, "root", skills=["@builtin/same"], profiles=["@other/project"])
    profile(two, "project", scope="project", skills=["@other/same"])
    catalog = Catalog(builtin=one,sources={"other":two})
    assert len(compose(catalog,"@builtin/root",agent="codex",project_root=tmp_path).skills) == 2
    with pytest.raises(ConfigurationError, match="project_root"):
        compose(catalog,"@builtin/root",agent="codex")


def test_reviewed_python_bundle(tmp_path):
    root = Path(__file__).resolve().parents[1] / ".pspec"
    catalog = Catalog(builtin=root)
    bundle = compose(catalog, "@builtin/python-simple-cli", agent="codex",
                     exclude_profiles=["@builtin/zmem-lifecycle", "@builtin/adhd-friendly"])
    assert {r.name for r in bundle.contexts} == {
        "archive-temporary-state", "python-simple-cli", "utility-plan", "utility-apply",
    }
    names = [t.resource.name for t in bundle.skills]
    assert names.count("pspec-tdd") == 1 and "pspec-bdd" not in names
    assert "pspec-plan-utilities" in names and "pspec-skill-bootstrap" in names
    assert bundle.selected_defaults["test_command"] == "uv run pytest"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("selected", [None, ""])
def test_empty_selection_composes_globals_and_exclusions(tmp_path, selected):
    skill(tmp_path, "shared", "shared")
    profile(tmp_path, "always", **{"global": True}, skills=["@builtin/shared"], vars={"mode": "global"})
    profile(tmp_path, "unused", skills=["@builtin/missing"], vars={"mode": "selected"})
    catalog = Catalog(builtin=tmp_path)
    bundle = compose(catalog, selected, agent="codex")
    assert [p.ref for p in bundle.profiles] == ["@builtin/always"]
    assert bundle.selected_defaults == {} and bundle.global_defaults == {"mode": "global"}
    assert [s.resource.name for s in bundle.skills] == ["shared"]
    empty = compose(catalog, selected, agent="codex", exclude_profiles=["@builtin/always"])
    assert empty.profiles == empty.skills == ()


def test_runtime_composition_retains_raw_skill_arming_without_materialization(tmp_path):
    profile(tmp_path, "always", **{"global": True},
            skills=["@gitsource/offline/skills/*"], vars={"language": "python"})
    catalog = Catalog(builtin=tmp_path, git_resolver=lambda _identity: (_ for _ in ()).throw(AssertionError()))
    bundle = compose(catalog, agent="codex", resolve_skills=False)
    assert bundle.skills == ()
    assert bundle.armed("skill", "@gitsource/offline/skills/*")
    assert bundle.global_defaults["language"] == "python"


def test_remote_same_name_conflicts_only_when_selected_for_same_target(tmp_path):
    builtin, one, two = tmp_path / "builtin", tmp_path / "one", tmp_path / "two"
    skill(one, "folder-one", "shared")
    skill(two, "folder-two", "shared")
    profile(builtin, "one", skills=["@gitsource/one/skills/*"])
    profile(builtin, "both", skills=["@gitsource/one/skills/*", "@gitsource/two/skills/*"])
    bindings = {
        "one": SourceBinding("one", "https://example.test/one", "main", "a" * 40,
                             "1" * 64, "one", one),
        "two": SourceBinding("two", "https://example.test/two", "main", "b" * 40,
                             "2" * 64, "two", two),
    }
    catalog = Catalog(builtin=builtin, gitsources=bindings)
    selected = compose(catalog, "@builtin/one", agent="codex")
    assert [target.resource.name for target in selected.skills] == ["shared"]
    with pytest.raises(ConfigurationError, match="skill target conflict.*gitsource/one.*gitsource/two"):
        compose(catalog, "@builtin/both", agent="codex")

    profile(builtin, "project", scope="project", skills=["@gitsource/two/skills/*"])
    profile(builtin, "scoped", profiles=["@builtin/one", "@builtin/project"])
    scoped = compose(Catalog(builtin=builtin, gitsources=bindings), "@builtin/scoped",
                     agent="codex", project_root=tmp_path)
    assert {(item.scope, item.resource.name) for item in scoped.skills} == {
        ("user", "shared"), ("project", "shared")
    }

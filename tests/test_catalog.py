from pathlib import Path
import pytest
from powerspec.catalog import Catalog, ConfigurationError
from powerspec.sources import SourceBinding


def write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_declared_identity_and_distinct_kinds(tmp_path):
    write(tmp_path, "skills/folder_name/SKILL.md", "---\nname: declared-name\ndescription: Test\n---\nBody")
    write(tmp_path, "contexts/shared.toml", '[[attach.context]]\nbody="text"')
    write(tmp_path, "traits/shared.toml", 'hooks=["sessionStart"]\nbody="text"')
    catalog = Catalog(builtin=tmp_path)
    skill = catalog.get("skill", "@builtin/declared-name")
    assert skill.path.parent.name == "folder_name"
    assert skill.name == "declared-name"
    assert skill.ref == "@builtin/declared-name"
    assert catalog.get("context", "@builtin/shared").kind == "context"
    assert catalog.get("trait", "@builtin/shared").kind == "trait"
    with pytest.raises(ConfigurationError):
        catalog.get("skill", "@builtin/folder_name")


def test_duplicate_names_and_reserved_source(tmp_path):
    for folder in ("a", "b"):
        write(tmp_path, f"skills/{folder}/SKILL.md", "---\nname: same\n---\n")
    with pytest.raises(ConfigurationError, match="duplicate"):
        Catalog(builtin=tmp_path)
    with pytest.raises(ConfigurationError, match="reserved"):
        Catalog(sources={"builtin": tmp_path})


@pytest.mark.parametrize("kind,body", [
    ("traits", 'mode="config"\n[[attach.context]]\nbody="x"'),
    ("traits", 'hooks=["sessionStart"]\nbody="x"\n[[compiletime]]\nid="x"\ntype="string"'),
    ("contexts", 'hooks=["sessionStart"]\nbody="x"'),
    ("profiles", 'scope="elsewhere"'),
    ("profiles", 'skills=[{name="@builtin/x",scope="user"}]'),
    ("profiles", 'hooks=["sessionStart"]'),
    ("traits", 'hooks=["sessionStart"]\nbody="x"\nwhen={check=true}'),
    ("traits", 'hooks=["sessionStart"]\nbody="x"\nwhen="not valid !!!"'),
    ("traits", 'hooks=["sessionStart"]\nbody="x"\n[[check]]\nid="old"'),
    ("contexts", '[[compiletime]]\nid="x"\ntype="string"\n[[compiletime.parser]]\ntype="prompt"'),
])
def test_invalid_resource_shapes(tmp_path, kind, body):
    write(tmp_path, f"{kind}/bad.toml", body)
    with pytest.raises(ConfigurationError, match="bad.toml"):
        Catalog(builtin=tmp_path)


def test_conditions_are_only_parsed_and_bodies_are_data(tmp_path):
    write(tmp_path, "traits/probe.toml", 'hooks=["sessionStart"]\nbody="1 / 0"\nwhen="missing_callback()"')
    value = Catalog(builtin=tmp_path).get("trait", "@builtin/probe")
    assert value.data["when"] == "missing_callback()"
    assert value.data["body"] == "1 / 0"


def test_materialized_remote_identity(tmp_path):
    write(tmp_path, "skills/folder/SKILL.md", "---\nname: named-skill\n---\n")
    catalog = Catalog(gitsources={"external": tmp_path})
    skills = catalog.select("skill", "@gitsource/external/skills/*")
    assert len(skills) == 1
    assert skills[0].name == "named-skill"
    assert skills[0].ref == "@gitsource/external/skills/folder"
    assert catalog.get("skill", skills[0].ref) == skills[0]


def test_direct_git_selection_is_lazy_deterministic_and_retains_provenance(tmp_path):
    write(tmp_path, "skills/z-last/SKILL.md", "---\nname: last\n---\n")
    write(tmp_path, "skills/a-first/SKILL.md", "---\nname: first\n---\n")
    write(tmp_path, "skills/not-a-skill/readme.md", "ignored")
    write(tmp_path, "unselected/bad/SKILL.md", "not frontmatter")
    binding = SourceBinding("tools", "https://example.test/tools", "main", "a" * 40,
                            "1" * 64, "artifact", tmp_path)
    catalog = Catalog(gitsources={"tools": binding})
    selected = catalog.select("skill", "@gitsource/tools/skills/*")
    assert [item.name for item in selected] == ["first", "last"]
    assert [item.ref for item in selected] == [
        "@gitsource/tools/skills/a-first", "@gitsource/tools/skills/z-last"
    ]
    assert selected[0].provenance == {
        "provider": "git", "source": "tools", "path": "skills/a-first",
        "repository": "https://example.test/tools", "requested_revision": "main",
        "resolved_revision": "a" * 40, "source_id": "1" * 64,
        "artifact_id": "artifact",
    }


def test_direct_and_recursive_git_selectors_have_explicit_depth(tmp_path):
    write(tmp_path, "skills/one/SKILL.md", "---\nname: one\n---\n")
    write(tmp_path, "skills/group/two/SKILL.md", "---\nname: two\n---\n")
    catalog = Catalog(gitsources={"tools": tmp_path})
    assert [item.name for item in catalog.select("skill", "@gitsource/tools/skills/*")] == ["one"]
    assert [item.name for item in catalog.select("skill", "@gitsource/tools/skills/**")] == ["two", "one"]
    assert catalog.select("skill", "@gitsource/tools/skills/group/two")[0].name == "two"


def test_git_materialization_is_resolved_lazily_for_selected_identity(tmp_path):
    write(tmp_path, "skills/one/SKILL.md", "---\nname: one\n---\n")
    calls = []

    def resolve(identity):
        calls.append(identity)
        return SourceBinding(identity, "https://example.test/tools", "main", "a" * 40,
                             "1" * 64, "artifact", tmp_path)

    catalog = Catalog(git_resolver=resolve)
    assert calls == []
    assert catalog.select("skill", "@gitsource/tools/skills/*")[0].name == "one"
    assert calls == ["tools"]
    catalog.select("skill", "@gitsource/tools/skills/one")
    assert calls == ["tools"]


def test_git_selector_rejects_unknown_empty_invalid_duplicate_and_escape(tmp_path):
    write(tmp_path, "skills/a/SKILL.md", "---\nname: same\n---\n")
    write(tmp_path, "skills/b/SKILL.md", "---\nname: same\n---\n")
    write(tmp_path, "invalid/bad/SKILL.md", "bad")
    (tmp_path / "empty").mkdir()
    catalog = Catalog(gitsources={"tools": tmp_path})
    with pytest.raises(ConfigurationError, match="missing Saucepan"):
        Catalog().select("skill", "@gitsource/unknown/skills/*")
    with pytest.raises(ConfigurationError, match="no materialized"):
        catalog.select("skill", "@gitsource/tools/empty/*")
    with pytest.raises(ConfigurationError, match="missing skill frontmatter"):
        catalog.select("skill", "@gitsource/tools/invalid/bad")
    with pytest.raises(ConfigurationError, match="duplicate selected skill"):
        catalog.select("skill", "@gitsource/tools/skills/*")
    with pytest.raises(ConfigurationError, match="malformed"):
        catalog.select("skill", "@gitsource/tools/../outside")

    outside = tmp_path.parent / "outside-skill"
    write(outside, "SKILL.md", "---\nname: outside\n---\n")
    link = tmp_path / "linked"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(str(error))
    with pytest.raises(ConfigurationError, match="escapes"):
        catalog.select("skill", "@gitsource/tools/linked")


def test_multiple_reusable_catalog_roots_share_one_source_namespace(tmp_path):
    first, second = tmp_path / "one/.pspec", tmp_path / "two/.pspec"
    write(first, "profiles/one.toml", 'scope="user"')
    write(second, "contexts/two.toml", '[[attach.context]]\nbody="two"')
    catalog = Catalog(sources={"team": (first, second)})
    assert catalog.get("profile", "@team/one").path.parent.parent == first.resolve()
    assert catalog.get("context", "@team/two").path.parent.parent == second.resolve()

    write(second, "profiles/one.toml", 'scope="user"')
    with pytest.raises(ConfigurationError, match="duplicate profile identity"):
        Catalog(sources={"team": (first, second)})


def test_symlink_resource_escape(tmp_path):
    root = tmp_path / "catalog"
    root.mkdir()
    outside = tmp_path / "outside.toml"
    outside.write_text('scope="user"')
    (root / "profiles").mkdir()
    try:
        (root / "profiles/escape.toml").symlink_to(outside)
    except OSError as error:
        pytest.skip(str(error))
    with pytest.raises(ConfigurationError, match="escapes"):
        Catalog(builtin=root)

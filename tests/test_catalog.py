from pathlib import Path
import pytest
from powerspec.catalog import Catalog, ConfigurationError


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

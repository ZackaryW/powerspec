from pathlib import Path

import pytest

from powerspec.catalog import ConfigurationError
from powerspec.skills import Dynamic, compose_document, read_document, section


ENTRY = """---
name: example
description: Example
---

# Procedure

Intro with <declared> and literal <skill:other>.

## Alpha

Alpha body.

### Child

Child body.

```markdown
## Alpha
```

## Beta

Beta body.

## Final

Final body.
"""


def put(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def dynamic(section, pos, path, source_section=None, when=None):
    return Dynamic(section=section, pos=pos, path=path,
                   source_section=source_section, when=when or {})


def test_exact_sections_include_descendants_and_ignore_fenced_headings(tmp_path):
    path = put(tmp_path, "SKILL.md", ENTRY)
    document = read_document("SKILL.md", root=tmp_path, entrypoint=True)
    assert not document.startswith("---")
    alpha = section(document, "Alpha", location=path)
    assert "### Child" in alpha.text and "## Beta" not in alpha.text
    with pytest.raises(ConfigurationError, match="missing"):
        section(document, "alpha", location=path)
    duplicated = document + "\n## Alpha\nagain\n"
    with pytest.raises(ConfigurationError, match="ambiguous"):
        section(duplicated, "Alpha", location=path)


def test_before_after_order_dedup_and_distinct_destinations(tmp_path):
    put(tmp_path, "SKILL.md", ENTRY)
    put(tmp_path, "parts.md", "# Parts\n\n## one\n\nOne.\n\n## two\n\nTwo.\n")
    items = [
        dynamic("Alpha", "before", "parts.md", "one"),
        dynamic("Alpha", "after", "parts.md", "one"),
        dynamic("Alpha", "after", "parts.md", "one"),
        dynamic("Alpha", "after", "parts.md", "two"),
        dynamic("Beta", "after", "parts.md", "one"),
    ]
    result = compose_document(tmp_path, "SKILL.md", items, {"declared": "VALUE"})
    assert result.index("<!-- Source: parts.md, section: one -->") < result.index("## Alpha")
    alpha_start = result.index("## Alpha")
    beta_start = result.index("## Beta")
    alpha = result[alpha_start:beta_start]
    assert alpha.count("Source: parts.md, section: one") == 1
    assert alpha.index("### Child") < alpha.index("## one") < alpha.index("## two")
    assert result[beta_start:].count("Source: parts.md, section: one") == 1
    assert "VALUE" in result and "<skill:other>" in result


def test_replace_last_active_wins_and_whole_file_selection(tmp_path):
    put(tmp_path, "SKILL.md", ENTRY)
    put(tmp_path, "a.md", "# A\n\nA body.\n")
    put(tmp_path, "b.md", "# B\n\nB body.\n")
    items = [
        dynamic("Alpha", "replace", "a.md"),
        dynamic("Alpha", "replace", "b.md"),
        dynamic("Alpha", "replace", "a.md"),
    ]
    result = compose_document(tmp_path, "SKILL.md", items, {})
    assert "\n# A\n" in result and "\n# B\n" not in result
    assert "Alpha body" not in result and "### Child" not in result
    assert "## Beta" in result


def test_combine_and_replace_reset_duplicate_history(tmp_path):
    put(tmp_path, "SKILL.md", ENTRY)
    for name in "ABCD":
        put(tmp_path, f"{name.lower()}.md", f"# {name}\n\n{name} body.\n")
    result = compose_document(tmp_path, "SKILL.md", [
        dynamic("Alpha", "replace", "a.md"),
        dynamic("Alpha", "combine", "b.md"),
        dynamic("Alpha", "replace", "c.md"),
        dynamic("Alpha", "combine", "d.md"),
    ], {})
    alpha = result[result.index("Source: c.md"):result.index("## Beta")]
    assert "# C" in alpha and "# D" in alpha
    assert "# A" not in alpha and "# B" not in alpha and "Alpha body" not in alpha

    reset = compose_document(tmp_path, "SKILL.md", [
        dynamic("Alpha", "combine", "a.md"),
        dynamic("Alpha", "replace", "b.md"),
        dynamic("Alpha", "combine", "a.md"),
        dynamic("Alpha", "combine", "a.md"),
    ], {})
    alpha = reset[reset.index("Source: b.md"):reset.index("## Beta")]
    assert alpha.count("Source: a.md") == 1 and "Alpha body" not in alpha


def test_first_combine_excludes_original(tmp_path):
    put(tmp_path, "SKILL.md", ENTRY)
    put(tmp_path, "a.md", "# A\n\nA.\n")
    result = compose_document(tmp_path, "SKILL.md", [dynamic("Final", "combine", "a.md")], {})
    assert "Final body" not in result and "# A" in result and "## Beta" in result


def test_ancestor_replacement_suppresses_child_in_any_declaration_order(tmp_path):
    put(tmp_path, "SKILL.md", ENTRY)
    put(tmp_path, "parent.md", "# Parent\n\nParent body.\n\n### Child\nReplacement child.\n")
    put(tmp_path, "child.md", "# Child edit\n\nShould not appear.\n")
    for items in ([
        dynamic("Child", "after", "child.md"),
        dynamic("Alpha", "replace", "parent.md"),
    ], [
        dynamic("Alpha", "replace", "parent.md"),
        dynamic("Child", "before", "child.md"),
    ]):
        result = compose_document(tmp_path, "SKILL.md", items, {})
        assert "Should not appear" not in result and "Replacement child" in result


def test_same_target_before_after_surround_replacement(tmp_path):
    put(tmp_path, "SKILL.md", ENTRY)
    put(tmp_path, "before.md", "Before marker.\n")
    put(tmp_path, "replace.md", "# Replacement\n")
    put(tmp_path, "after.md", "After marker.\n")
    result = compose_document(tmp_path, "SKILL.md", [
        dynamic("Alpha", "after", "after.md"),
        dynamic("Alpha", "replace", "replace.md"),
        dynamic("Alpha", "before", "before.md"),
    ], {})
    assert result.index("Before marker") < result.index("# Replacement") < result.index("After marker") < result.index("## Beta")


def test_single_pass_substitution_and_unknown_prose(tmp_path):
    put(tmp_path, "SKILL.md", ENTRY)
    put(tmp_path, "python.md", "# Selected\n\nUse <command>. Literal <unknown>. Value does not recurse: <nested>.\n")
    result = compose_document(tmp_path, "SKILL.md", [dynamic("Beta", "after", "<language>.md")],
                              {"declared": "x", "language": "python", "command": "uv run pytest", "nested": "<command>"})
    assert "Use uv run pytest" in result
    assert "Literal <unknown>" in result
    assert "Value does not recurse: <command>" in result


@pytest.mark.parametrize("relative", ["../outside.md", "<missing>.md"])
def test_invalid_or_unknown_selected_path_fails(tmp_path, relative):
    put(tmp_path, "SKILL.md", ENTRY)
    with pytest.raises((ConfigurationError, ValueError)):
        compose_document(tmp_path, "SKILL.md", [dynamic("Alpha", "after", relative)], {})


def test_missing_active_file_or_sections_never_returns_partial(tmp_path):
    put(tmp_path, "SKILL.md", ENTRY)
    put(tmp_path, "source.md", "# Existing\n")
    cases = [
        dynamic("Alpha", "after", "missing.md"),
        dynamic("Missing", "after", "source.md"),
        dynamic("Alpha", "after", "source.md", "missing"),
    ]
    for item in cases:
        result = None
        with pytest.raises(ConfigurationError):
            result = compose_document(tmp_path, "SKILL.md", [item], {})
        assert result is None


def test_symlink_escape_is_rejected(tmp_path):
    put(tmp_path, "SKILL.md", ENTRY)
    outside = put(tmp_path.parent, "outside-skill.md", "# Outside\n")
    link = tmp_path / "linked.md"
    try:
        link.symlink_to(outside)
    except OSError as error:
        pytest.skip(str(error))
    with pytest.raises(ConfigurationError, match="escapes"):
        compose_document(tmp_path, "SKILL.md", [dynamic("Alpha", "after", "linked.md")], {})

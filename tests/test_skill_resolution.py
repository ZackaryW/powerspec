from types import SimpleNamespace

from powerspec.consumer import discover_consumer
from powerspec.skills import resolve_skill


def put(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def empty_bundle(**selected):
    return SimpleNamespace(selected_defaults=selected, global_defaults={})


def skill(root):
    put(root / "SKILL.md", """---
name: branch-skill
description: Test branch resolution.
---

# Flow

Use <mode>.

## Work

Shared.
""")
    put(root / "pspec.toml", """
version = 1
entry = "SKILL.md"

[[input]]
id = "mode"
type = "string"
choices = ["python", "rust"]
[[input.parser]]
type = "prompt"
prompt = "Which mode?"
default = "python"

[[input]]
id = "command"
type = "string"
when = { mode = "python" }
[[input.parser]]
type = "prompt"
prompt = "Which command?"

[[dynamic]]
section = "Work"
pos = "after"
path = "languages/python.md"
source_section = "details"
when = { mode = "python" }

[[dynamic]]
section = "Work"
pos = "after"
path = "languages/rust.md"
when = { mode = "rust" }
""")
    put(root / "languages/python.md", "## details\n\nRun <command>.\n")


def test_pending_withholds_procedure_and_exposes_only_reachable_questions(tmp_path):
    root = tmp_path / "skill"
    skill(root)
    result = resolve_skill(root, empty_bundle(), None)
    assert result.status == "pending" and result.content is None
    assert [question.key for question in result.questions] == ["mode"]
    assert result.questions[0].suggested == "python"


def test_false_branch_does_not_read_absent_source_or_request_python_input(tmp_path):
    root = tmp_path / "skill"
    skill(root)
    (root / "languages/python.md").unlink()
    put(root / "languages/rust.md", "Rust guidance.\n")
    result = resolve_skill(root, empty_bundle(mode="rust"), None)
    assert result.status == "resolved"
    assert "Use rust" in result.content
    assert "Rust guidance" in result.content
    assert result.questions == ()


def test_selected_source_discovers_content_inputs_and_resolves_document(tmp_path):
    root = tmp_path / "skill"
    skill(root)
    result = resolve_skill(root, empty_bundle(mode="python", command="uv run pytest"), None)
    assert result.status == "resolved"
    assert "Use python" in result.content
    assert "Run uv run pytest" in result.content
    assert "Source: languages/python.md, section: details" in result.content


def test_change_scoped_answer_changes_only_that_resolution(tmp_path):
    root = tmp_path / "skill"
    skill(root)
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    put(repo / "openspec/.pspec/config.toml", "[vars]\nmode=\"python\"\n")
    put(repo / "openspec/.pspec/current.toml", """
[_change.one]
command = "uv run pytest"

[_change.two]
command = "python -m pytest"
""")
    consumer = discover_consumer(repo)
    one = resolve_skill(root, empty_bundle(), consumer, change="one")
    two = resolve_skill(root, empty_bundle(), consumer, change="two")
    shared = resolve_skill(root, empty_bundle(), consumer)
    assert "uv run pytest" in one.content
    assert "python -m pytest" in two.content
    assert shared.status == "pending" and shared.questions[0].key == "command"
    assert shared.questions[0].answer_location.endswith("current.toml#vars")

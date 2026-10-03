from pathlib import Path
from types import SimpleNamespace

import pytest

from powerspec.catalog import ConfigurationError
from powerspec.skills import load_manifest, resolve_inputs


def write_manifest(root: Path, text: str):
    root.mkdir(parents=True, exist_ok=True)
    path = root / "pspec.toml"
    path.write_text(text, encoding="utf-8")
    return path


def bundle(selected=None, global_=None):
    return SimpleNamespace(selected_defaults=selected or {}, global_defaults=global_ or {})


def test_manifest_parses_version_two_inputs_guards_prompt_and_dynamic(tmp_path):
    path = write_manifest(tmp_path, '''
version = 2
entry = "SKILL.md"
[[input]]
id = "language"
type = "string"
choices = ["python", "rust"]
[input.parser]
type = "prompt"
prompt = "Language?"
default = "python"
[[input]]
id = "test_runner"
type = "string"
when = { language = "python" }
[input.parser]
type = "prompt"
prompt = "Runner?"
[[dynamic]]
section = "Red"
pos = "after"
path = "languages/<language>.md"
source_section = "red"
when = { language = "python" }
''')
    manifest = load_manifest(path)
    assert manifest.version == 2 and manifest.entry == "SKILL.md"
    assert manifest.input[0].parser.prompt == "Language?"
    assert manifest.input[1].when == {"language": "python"}
    assert manifest.dynamic[0].pos == "after"


@pytest.mark.parametrize("body,match", [
    ('version=1\nentry="SKILL.md"', "migrate to version 2"),
    ('version=2\nentry="SKILL.md"\nunknown=true', "unknown"),
    ('version=2\nentry="SKILL.md"\n[[hint]]\nid="x"\ntype="file-exists"\nfile_exists="x"\nvalue="x"', "removed.*hint"),
    ('version=2\nentry="SKILL.md"\n[[dynamic]]\nsection="A"\npos="before"\npath="x.md"', "removed.*before"),
    ('version=2\nentry="SKILL.md"\n[[dynamic]]\nsection="A"\npos="combine"\npath="x.md"', "removed.*combine"),
    ('version=2\nentry="SKILL.md"\n[[dynamic]]\nsection="A"\npos="insert,3"\npath="x.md"', "pos"),
    ('version=2\nentry="SKILL.md"\n[[dynamic]]\nsection="A"\npos="after"\npath="<missing>.md"', "missing"),
    ('version=2\nentry="SKILL.md"\n[[input]]\nid="x"\ntype="string"\nwhen={missing="x"}', "missing"),
    ('version=2\nentry="SKILL.md"\n[[input]]\nid="x"\ntype="string"\n[input.parser]\ntype="prompt"\nprompt="x"\ndefault_hint="nope"', "removed.*default_hint"),
    ('version=2\nentry="SKILL.md"\n[[input]]\nid="x"\ntype="string"\n[[input.parser]]\ntype="prompt"\nprompt="one"\n[[input.parser]]\ntype="prompt"\nprompt="two"', "one prompt parser"),
    ('version=2\nentry="SKILL.md"\n[[input]]\nid="x"\ntype="integer"\ndefault=true', "integer"),
    ('version=2\nentry="SKILL.md"\n[[input]]\nid="x"\ntype="string"\nwhen={y="yes"}\n[[input]]\nid="y"\ntype="string"\nwhen={x="yes"}', "cycle"),
])
def test_manifest_errors_are_resource_specific(tmp_path, body, match):
    path = write_manifest(tmp_path, body)
    with pytest.raises(ConfigurationError, match=match):
        load_manifest(path)


def test_configured_values_win_and_invalid_values_do_not_fallback(tmp_path):
    manifest = load_manifest(write_manifest(tmp_path, '''
version=2
entry="SKILL.md"
[[input]]
id="language"
type="string"
choices=["python","rust"]
default="rust"
[input.parser]
type="prompt"
prompt="Language?"
default="python"
[[dynamic]]
section="A"
pos="after"
path="languages/<language>.md"
'''))
    result = resolve_inputs(manifest, bundle(selected={"language": "python"}), None,
                            needed={"language"}, change=None)
    assert result.values == {"language": "python"} and result.questions == ()
    with pytest.raises(ConfigurationError, match="language"):
        resolve_inputs(manifest, bundle(selected={"language": "invalid"}), None,
                       needed={"language"}, change=None)
    defaulted = resolve_inputs(manifest, bundle(), None, needed={"language"}, change=None)
    assert defaulted.values == {"language": "rust"} and defaulted.questions == ()


def test_false_guard_skips_dependent_inputs_and_non_python_tooling(tmp_path):
    manifest = load_manifest(write_manifest(tmp_path, '''
version=2
entry="SKILL.md"
[[input]]
id="language"
type="string"
[input.parser]
type="prompt"
prompt="Language?"
[[input]]
id="test_command"
type="string"
when={language="python"}
[input.parser]
type="prompt"
prompt="Test command?"
'''))
    result = resolve_inputs(manifest, bundle(selected={"language": "rust"}), None,
                            needed={"test_command"}, change=None)
    assert result.values == {"language": "rust"}
    assert result.questions == ()


def test_missing_controller_is_pending_before_its_dependency(tmp_path):
    manifest = load_manifest(write_manifest(tmp_path, '''
version=2
entry="SKILL.md"
[[input]]
id="language"
type="string"
choices=["python","rust"]
[input.parser]
type="prompt"
prompt="Language?"
default="python"
[[input]]
id="test_command"
type="string"
when={language="python"}
[input.parser]
type="prompt"
prompt="Command?"
'''))
    result = resolve_inputs(manifest, bundle(), None, needed={"test_command"}, change="one")
    assert [q.key for q in result.questions] == ["language"]
    assert result.questions[0].suggested == "python"
    assert result.questions[0].change == "one"


def test_prompt_default_is_only_a_suggestion(tmp_path):
    manifest = load_manifest(write_manifest(tmp_path, '''
version=2
entry="SKILL.md"
[[input]]
id="test_runner"
type="string"
choices=["pytest","unittest"]
[input.parser]
type="prompt"
prompt="Runner?"
default="unittest"
'''))
    result = resolve_inputs(manifest, bundle(), None, needed={"test_runner"}, change=None)
    assert result.values == {}
    assert len(result.questions) == 1
    assert result.questions[0].suggested == "unittest"
    assert result.questions[0].has_suggestion
    assert result.questions[0].answer_location is None


def test_input_without_parser_uses_generic_pending_question(tmp_path):
    manifest = load_manifest(write_manifest(tmp_path, '''
version=2
entry="SKILL.md"
[[input]]
id="language"
type="string"
'''))
    result = resolve_inputs(manifest, bundle(), None, needed={"language"}, change=None)
    assert result.values == {}
    assert result.questions[0].prompt == "Supply language"
    assert not result.questions[0].has_suggestion

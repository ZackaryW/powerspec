import json
import os
from pathlib import Path
import shutil
import subprocess
import sysconfig

from typer.testing import CliRunner


def invoke(args):
    from powerspec.cli import app

    return CliRunner().invoke(app, args)


def put(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def installed(home: Path, name="example", *, manifest=None, default=None):
    root = home / ".codex/skills" / name
    put(root / "SKILL.md", f"""---
name: {name}
description: Example.
---

# Procedure

Use <language>.
""")
    if manifest is not None:
        put(root / "pspec.toml", manifest)
    elif default is not None:
        put(root / "pspec.toml", f"""
version = 2
entry = "SKILL.md"
[[input]]
id = "language"
type = "string"
default = "{default}"
""")
    return root


def environment(tmp_path, monkeypatch):
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("CODEX_HOME", str(home / ".codex"))
    monkeypatch.chdir(project)
    return home, project


def snapshot(root: Path):
    return {
        path.relative_to(root).as_posix(): path.read_bytes() if path.is_file() else None
        for path in root.rglob("*")
    }


def console(name):
    suffix = ".exe" if os.name == "nt" else ""
    return str(Path(sysconfig.get_path("scripts")) / (name + suffix))


def test_empty_consumer_profile_resolves_global_defaults(tmp_path, monkeypatch):
    from contextlib import contextmanager
    import importlib
    home, project = environment(tmp_path, monkeypatch)
    installed(home, default="fallback")
    (project / ".git").mkdir()
    put(project / "openspec/.pspec/config.toml", 'profile=""\n')
    catalog = tmp_path / "catalog"
    put(catalog / "profiles/global.toml", 'global=true\n[vars]\nlanguage="python"\n')
    @contextmanager
    def resources():
        yield catalog
    monkeypatch.setattr(importlib.import_module("powerspec.cli.skill"), "builtin_catalog_root", resources)
    result = invoke(["resolve", "skill", "--path", str(home / ".codex/skills/example"), "--agent", "codex"])
    assert result.exit_code == 0 and "Use python." in result.stdout, result.output


def test_installed_skill_resolution_does_not_require_global_remote_materialization(tmp_path, monkeypatch):
    from contextlib import contextmanager
    import importlib
    home, project = environment(tmp_path, monkeypatch)
    installed(home, default="fallback")
    (project / ".git").mkdir()
    put(project / "openspec/.pspec/config.toml", '[vars]\n')
    catalog = tmp_path / "catalog"
    put(catalog / "profiles/global.toml",
        'global=true\nskills=["offline/skills/*"]\n'
        '[[source]]\nid="offline"\nprovider="git"\n'
        'origin="https://example.test/offline"\nreference="main"\n'
        '[vars]\nlanguage="python"\n')
    @contextmanager
    def resources():
        yield catalog
    monkeypatch.setattr(importlib.import_module("powerspec.cli.skill"), "builtin_catalog_root", resources)
    result = invoke(["resolve", "skill", "--path", str(home / ".codex/skills/example"), "--agent", "codex"])
    assert result.exit_code == 0 and "Use python." in result.stdout, result.output


def test_located_skill_without_manifest_returns_literal_null(tmp_path, monkeypatch):
    home, _ = environment(tmp_path, monkeypatch)
    installed(home, manifest=None)
    before = snapshot(tmp_path)
    for extra in ([], ["--json"]):
        result = invoke(["resolve", "skill", "--path", str(home / ".codex/skills/example"), "--agent", "codex", *extra])
        assert result.exit_code == 0 and result.stdout == "null\n" and result.stderr == ""
    assert snapshot(tmp_path) == before


def test_resolved_markdown_and_json_have_identical_content(tmp_path, monkeypatch):
    home, _ = environment(tmp_path, monkeypatch)
    installed(home, default="python")
    before = snapshot(tmp_path)
    markdown = invoke(["resolve", "skill", "--path", str(home / ".codex/skills/example"), "--agent", "codex"])
    structured = invoke(["resolve", "skill", "--path", str(home / ".codex/skills/example"), "--agent", "codex", "--json"])
    assert markdown.exit_code == structured.exit_code == 0
    payload = json.loads(structured.stdout)
    assert payload["status"] == "resolved" and payload["content"] == markdown.stdout
    assert "Use python" in markdown.stdout and snapshot(tmp_path) == before


def test_both_installed_aliases_resolve_the_same_content(tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    installed(home, default="python")
    environment_vars = {
        **os.environ,
        "HOME": str(home),
        "USERPROFILE": str(home),
        "CODEX_HOME": str(home / ".codex"),
        "NO_COLOR": "1",
        "TERM": "dumb",
    }
    outputs = []
    for name in ("pspec", "powerspec"):
        result = subprocess.run(
            [console(name), "resolve", "skill", "--path", str(home / ".codex/skills/example"), "--agent", "codex"],
            cwd=project,
            env=environment_vars,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0 and result.stderr == ""
        outputs.append(result.stdout)
    assert outputs == [outputs[0], outputs[0]] and "Use python" in outputs[0]


def test_pending_withholds_content_and_describes_scoped_rerun(tmp_path, monkeypatch):
    home, project = environment(tmp_path, monkeypatch)
    installed(home, manifest="""
version = 2
entry = "SKILL.md"
[[input]]
id = "language"
type = "string"
choices = ["python", "rust"]
[input.parser]
type = "prompt"
prompt = "Which language?"
default = "python"
""")
    (project / ".git").mkdir()
    put(project / "openspec/.pspec/config.toml", 'exclude-profiles=["@builtin/zmem-lifecycle", "@builtin/adhd-friendly"]\n')
    result = invoke(["resolve", "skill", "--path", str(home / ".codex/skills/example"), "--agent", "codex", "--change", "work"])
    assert result.exit_code == 0 and "resolution pending" in result.stdout
    assert "Use <language>" not in result.stdout
    assert "Suggested value: `python`" in result.stdout
    assert "current.toml#_change.work" in result.stdout
    assert "--change work" in result.stdout

    structured = invoke(["resolve", "skill", "--path", str(home / ".codex/skills/example"), "--agent", "codex", "--change", "work", "--json"])
    payload = json.loads(structured.stdout)
    assert payload["status"] == "pending" and "content" not in payload
    assert payload["questions"][0]["key"] == "language"
    assert payload["questions"][0]["suggested"] == "python"


def test_change_answer_resolves_without_affecting_another_change(tmp_path, monkeypatch):
    home, project = environment(tmp_path, monkeypatch)
    installed(home, manifest="""
version = 2
entry = "SKILL.md"
[[input]]
id = "language"
type = "string"
[input.parser]
type = "prompt"
prompt = "Which language?"
""")
    (project / ".git").mkdir()
    put(project / "openspec/.pspec/config.toml", 'exclude-profiles=["@builtin/zmem-lifecycle", "@builtin/adhd-friendly"]\n')
    put(project / "openspec/.pspec/current.toml", "[_change.one]\nlanguage=\"python\"\n")
    resolved = invoke(["resolve", "skill", "--path", str(home / ".codex/skills/example"), "--agent", "codex", "--change", "one"])
    pending = invoke(["resolve", "skill", "--path", str(home / ".codex/skills/example"), "--agent", "codex", "--change", "two"])
    assert resolved.exit_code == pending.exit_code == 0
    assert "Use python" in resolved.stdout and "resolution pending" in pending.stdout


def test_selected_path_resolves_codex_coexistence(tmp_path, monkeypatch):
    home, project = environment(tmp_path, monkeypatch)
    installed(home, default="user")
    local = project / ".agents/skills/example"
    put(local / "SKILL.md", "---\nname: example\ndescription: Local.\n---\n\n# Local\n")
    without = invoke(["resolve", "skill", "--path", str(home / ".codex/skills/example"), "--agent", "codex"])
    assert without.exit_code == 0 and "user" in without.stdout
    chosen = invoke(["resolve", "skill", "--path", str(local), "--agent", "codex"])
    assert chosen.exit_code == 0 and chosen.stdout == "null\n"


def test_malformed_manifest_is_error_without_success_payload(tmp_path, monkeypatch):
    home, _ = environment(tmp_path, monkeypatch)
    installed(home, manifest='version = 1\nentry = "SKILL.md"\n')
    result = invoke(["resolve", "skill", "--path", str(home / ".codex/skills/example"), "--agent", "codex", "--json"])
    assert result.exit_code == 1 and result.stdout == ""
    assert "pspec.toml" in result.stderr and "version" in result.stderr


def test_authored_python_tdd_profile_resolves_complete_document(tmp_path, monkeypatch):
    home, project = environment(tmp_path, monkeypatch)
    source = Path(__file__).resolve().parents[1] / ".pspec/skills/pspec-tdd"
    installed_root = home / ".codex/skills/pspec-tdd"
    shutil.copytree(source, installed_root)
    (project / ".git").mkdir()
    put(project / "openspec/.pspec/config.toml", """
profile = "@builtin/python-simple-cli"
exclude-profiles = ["@builtin/zmem-lifecycle", "@builtin/adhd-friendly"]
""")
    before = snapshot(tmp_path)
    markdown = invoke(["resolve", "skill", "--path", str(installed_root), "--agent", "codex"])
    structured = invoke(["resolve", "skill", "--path", str(installed_root), "--agent", "codex", "--json"])
    assert markdown.exit_code == structured.exit_code == 0
    payload = json.loads(structured.stdout)
    assert payload["status"] == "resolved" and payload["content"] == markdown.stdout
    assert all(value in markdown.stdout for value in (
        "## scope", "## red", "## green", "uv run pytest",
        "## Refactor and repeat", "## Return evidence to the caller",
    ))
    assert "# Powerspec skill resolution pending" not in markdown.stdout
    assert "bdd" not in markdown.stdout.lower()
    example = (Path(__file__).resolve().parents[1] / "docs/examples/tdd-python-resolution.md").read_text(
        encoding="utf-8"
    )
    recorded = example.split("```markdown\n", 1)[1].split("\n```", 1)[0] + "\n"
    assert markdown.stdout == recorded
    assert snapshot(tmp_path) == before

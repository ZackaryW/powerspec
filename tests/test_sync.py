from pathlib import Path
from types import SimpleNamespace
import os
import subprocess
import sysconfig

import yaml
from typer.testing import CliRunner

from powerspec.catalog import ConfigurationError
from powerspec.sources import SourceBinding
from powerspec.syncing import publish, reconcile


def contribution(destination, body, identifier):
    return SimpleNamespace(destination=destination, body=body, identifier=identifier)


def put(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def invoke(args):
    from powerspec.cli import app

    return CliRunner().invoke(app, args)


def console(name):
    suffix = ".exe" if os.name == "nt" else ""
    return str(Path(sysconfig.get_path("scripts")) / (name + suffix))


def test_global_contexts_sync_without_a_selected_profile(tmp_path, monkeypatch):
    from contextlib import contextmanager
    import importlib
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    put(project / "openspec/.pspec/config.toml", '[vars]\n')
    target = put(project / "openspec/config.yaml", 'schema: spec-driven\n')
    catalog = tmp_path / "catalog"
    put(catalog / "profiles/global.toml", 'global=true\ncontexts=["@builtin/global"]\n')
    put(catalog / "contexts/global.toml", '[[attach.context]]\nbody="Global guidance"\n')
    @contextmanager
    def resources():
        yield catalog
    monkeypatch.setattr(importlib.import_module("powerspec.cli.sync"), "builtin_catalog_root", resources)
    monkeypatch.chdir(project)
    result = invoke(["sync"])
    assert result.exit_code == 0, result.output
    assert "Global guidance" in target.read_text()


def test_sync_reuses_existing_remote_materialization_without_acquisition(tmp_path, monkeypatch):
    from contextlib import contextmanager
    import importlib
    module = importlib.import_module("powerspec.cli.sync")
    project = tmp_path / "project"
    remote = tmp_path / "remote"
    (project / ".git").mkdir(parents=True)
    put(project / "openspec/.pspec/config.toml", '[vars]\n')
    target = put(project / "openspec/config.yaml", 'schema: spec-driven\n')
    catalog = tmp_path / "catalog"
    put(catalog / "profiles/global.toml",
        'global=true\nskills=["@gitsource/tools/skills/*"]\ncontexts=["@builtin/global"]\n')
    put(catalog / "contexts/global.toml", '[[attach.context]]\nbody="Remote-aware guidance"\n')
    put(remote / "skills/tool/SKILL.md", '---\nname: tool\ndescription: Tool.\n---\n')
    calls = []

    class Sources:
        def lookup(self, identity):
            calls.append(("lookup", identity))
            return SourceBinding(identity, "https://example.test/tools", "main", "a" * 40,
                                 "1" * 64, "artifact", remote)

        def acquire(self, identity):
            calls.append(("acquire", identity))
            raise AssertionError("sync acquired a source")

    @contextmanager
    def resources():
        yield catalog

    monkeypatch.setattr(module, "builtin_catalog_root", resources)
    monkeypatch.setattr(module, "SaucepanSources", Sources)
    monkeypatch.chdir(project)
    result = invoke(["sync"])
    assert result.exit_code == 0, result.output
    assert calls == [("lookup", "tools")]
    assert "Remote-aware guidance" in target.read_text()


def test_sync_missing_required_remote_preserves_yaml(tmp_path, monkeypatch):
    from contextlib import contextmanager
    import importlib
    module = importlib.import_module("powerspec.cli.sync")
    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    put(project / "openspec/.pspec/config.toml", '[vars]\n')
    target = put(project / "openspec/config.yaml", 'schema: spec-driven\ncontext: Keep me.\n')
    publish(target, [contribution("context", "Obsolete managed guidance", "@builtin/old/context/1")])
    catalog = tmp_path / "catalog"
    put(catalog / "profiles/global.toml", 'global=true\nskills=["@gitsource/offline/skills/*"]\n')

    class Sources:
        def lookup(self, identity):
            raise ConfigurationError(f"Saucepan source {identity!r} is unavailable")

    @contextmanager
    def resources():
        yield catalog

    monkeypatch.setattr(module, "builtin_catalog_root", resources)
    monkeypatch.setattr(module, "SaucepanSources", Sources)
    monkeypatch.chdir(project)
    result = invoke(["sync"])
    assert result.exit_code == 1 and "unavailable" in result.stderr
    text = target.read_text()
    assert "Keep me" in text and "Obsolete managed guidance" not in text


def test_reconcile_preserves_user_content_and_replaces_managed_entries():
    original = b"""# keep comment
schema: spec-driven
context: |
  User context.
rules:
  tasks:
    - User task rule.
operations:
  apply:
    guidance:
      - User apply guidance.
custom: value
"""
    contributions = [
        contribution("context", "Generated context.", "@builtin/example/context/1"),
        contribution("rules.tasks", "Generated task.", "@builtin/example/rules.tasks/1"),
        contribution("operations.apply.guidance", "Generated apply.", "@builtin/example/operations.apply.guidance/1"),
    ]
    first = reconcile(original, contributions)
    text = first.decode()
    assert text.startswith("# keep comment") and "custom: value" in text
    assert "User context" in text and "Generated context" in text
    assert "^@builtin/example/context/1" in text
    parsed = yaml.safe_load(first)
    assert parsed["rules"]["tasks"][0] == "User task rule."
    assert "Generated task" in parsed["rules"]["tasks"][1]
    assert parsed["operations"]["apply"]["guidance"][0] == "User apply guidance."
    assert reconcile(first, contributions) == first

    removed = reconcile(first, [])
    removed_text = removed.decode()
    assert "Generated" not in removed_text and "pspec:managed" not in removed_text
    assert "User context" in removed_text and "User task rule" in removed_text


def test_reconcile_rejects_ambiguous_markers_and_incompatible_destinations():
    bad = b"schema: spec-driven\ncontext: |\n  <!-- pspec:contexts:start -->\n"
    try:
        reconcile(bad, [])
    except ConfigurationError as error:
        assert "markers" in str(error)
    else:
        raise AssertionError("unbalanced marker accepted")
    try:
        reconcile(b"schema: spec-driven\nrules: text\n", [])
    except ConfigurationError as error:
        assert "rules" in str(error)
    else:
        raise AssertionError("incompatible rules accepted")
    malformed_entry = b"schema: spec-driven\nrules:\n  tasks:\n    - |\n      text\n      <!-- pspec:managed -->\n"
    try:
        reconcile(malformed_entry, [])
    except ConfigurationError as error:
        assert "managed entry" in str(error)
    else:
        raise AssertionError("malformed managed entry accepted")


def test_sync_publishes_reviewed_contexts_then_is_unchanged(tmp_path, monkeypatch):
    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    config = put(project / "openspec/.pspec/config.toml", """
profile = "@builtin/python-simple-cli"
exclude-profiles = ["@builtin/zmem-lifecycle", "@builtin/adhd-friendly"]
[vars]
utility_path = "src/example/utils"
""")
    current = put(config.parent / "current.toml", "invalid = [")
    target = put(project / "openspec/config.yaml", """# handwritten
schema: spec-driven
context: |
  Keep this project note.
rules:
  tasks:
    - Keep this task rule.
""")
    before_current = current.read_bytes()
    monkeypatch.chdir(project)

    first = invoke(["sync"])
    assert first.exit_code == 0 and first.stdout.startswith("updated:"), first.output
    published = target.read_bytes()
    text = published.decode()
    assert all(value in text for value in (
        "Keep this project note", "src/example/utils", "uv run pytest",
        "^@builtin/python-simple-cli/context/1",
        "^@builtin/utility-plan/rules.design/1",
        "^@builtin/utility-apply/operations.apply.guidance/1",
    ))
    assert "mature-package-inspection" not in text
    assert current.read_bytes() == before_current

    second = invoke(["sync"])
    assert second.exit_code == 0 and second.stdout.startswith("unchanged:")
    assert target.read_bytes() == published

    config.write_text("""
profile = "@builtin/builtin"
exclude-profiles = ["@builtin/zmem-lifecycle", "@builtin/adhd-friendly"]
""", encoding="utf-8")
    third = invoke(["sync"])
    assert third.exit_code == 0 and "updated:" in third.stdout
    final = target.read_text(encoding="utf-8")
    assert "src/example/utils" not in final and "Keep this project note" in final


def test_publication_failure_preserves_original_and_cleans_staging(tmp_path, monkeypatch):
    target = put(tmp_path / "config.yaml", "schema: spec-driven\n")
    original = target.read_bytes()
    import powerspec.syncing as syncing

    def fail(source, destination):
        raise OSError("controlled replacement failure")

    monkeypatch.setattr(syncing.os, "replace", fail)
    try:
        publish(target, [contribution("context", "body", "@builtin/x/context/1")])
    except ConfigurationError as error:
        assert "publication failed" in str(error)
    else:
        raise AssertionError("publication failure reported success")
    assert target.read_bytes() == original
    assert list(tmp_path.glob(".config.yaml.pspec-*")) == []


def test_both_installed_aliases_expose_sync(tmp_path):
    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    put(project / "openspec/.pspec/config.toml", """
profile = "@builtin/builtin"
exclude-profiles = ["@builtin/zmem-lifecycle", "@builtin/adhd-friendly"]
""")
    put(project / "openspec/config.yaml", "schema: spec-driven\n")
    results = [subprocess.run(
        [console(name), "sync"], cwd=project, capture_output=True, text=True,
        env={**os.environ, "NO_COLOR": "1", "TERM": "dumb"}, timeout=15,
    ) for name in ("pspec", "powerspec")]
    assert all(result.returncode == 0 and result.stderr == "" for result in results)
    assert results[0].stdout.startswith(("updated:", "unchanged:"))
    assert results[1].stdout.startswith("unchanged:")

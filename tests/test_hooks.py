import json
import subprocess
import re
import sys
from copy import deepcopy

import pytest
from typer.testing import CliRunner

from powerspec.catalog import Catalog, ConfigurationError
from powerspec.hooks import (
    callback_for, dispatch, matching_traits, native_document, selected_callbacks,
    serialize,
)
from powerspec.profiles import compose
from powerspec.provisioning import provision_hooks


def put(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.parametrize('selector', ['remote/skills/folder', 'remote/skills/*'])
def test_remote_mentions_use_declared_names_fresh_readonly_evidence(tmp_path, selector):
    from powerspec.catalog import MetadataUnavailable
    project = consumer(tmp_path)
    root = tmp_path / 'catalog'
    remote = tmp_path / 'remote'
    put(root, 'profiles/main.toml', 'traits=["@builtin/guide", "@builtin/independent"]\n'
        f'skills=["{selector}"]\n[[source]]\nid="remote"\nprovider="git"\n'
        'origin="https://example.test/tools"\nreference="main"')
    put(root, 'traits/guide.toml', 'hooks=["sessionStart"]\nbody="Use <skill:declared> twice: <skill:declared>."')
    put(root, 'traits/independent.toml', 'hooks=["sessionStart"]\nbody="Independent guidance."')
    put(remote, 'skills/folder/SKILL.md', '---\nname: declared\n---\n')
    manifest = put(remote, 'skills/folder/pspec.toml', 'version=2\nentry="SKILL.md"')
    calls = []
    available = False
    def lookup(source, recipe, *, deadline):
        import time
        assert 0 < deadline - time.monotonic() <= 1
        calls.append(source)
        if not available:
            raise MetadataUnavailable('service unavailable')
        return remote
    configured = Catalog(builtin=root, git_resolver=lookup)
    diagnostics = []
    def run():
        return dispatch(logical_event='sessionStart', agent='codex', cwd=project,
                        catalog=configured, diagnostics=diagnostics)
    assert 'Skill metadata unavailable: declared' in run()
    assert diagnostics == ['service unavailable']
    available = True
    output = run()
    assert 'Skills requiring dynamic resolution: declared\n' in output
    assert output.endswith('Independent guidance.')
    assert calls == ['remote', 'remote']
    manifest.write_text('version=1')
    with pytest.raises(ConfigurationError, match='manifest version'):
        run()
    manifest.unlink()
    configured.resources['trait', '@builtin/guide'].data['body'] = 'Use <skill:folder>.'
    with pytest.raises(ConfigurationError, match='unknown selected skill reference folder'):
        run()


def test_ineligible_and_no_reference_traits_never_inspect_remote(tmp_path):
    project = consumer(tmp_path)
    root, _ = catalog(tmp_path, 'hooks=["sessionStart"]\nbody="Use <skill:bad>."\nwhen="False"')
    put(root, 'profiles/main.toml', 'traits=["@builtin/guide"]\nskills=["remote/*"]\n'
        '[[source]]\nid="remote"\nprovider="git"\norigin="https://example.test/tools"\nreference="main"')
    configured = Catalog(builtin=root, git_resolver=lambda *a, **kw: pytest.fail('lookup'))
    assert dispatch(logical_event='sessionStart', agent='codex', cwd=project, catalog=configured) is None
    configured.resources['trait', '@builtin/guide'].data.update(body='Independent.', when='True')
    assert dispatch(logical_event='sessionStart', agent='codex', cwd=project, catalog=configured) == 'Independent.'


def test_dispatch_budget_exhaustion_does_not_retry_or_suppress_known_guidance(tmp_path, monkeypatch):
    import powerspec.skill_references as references
    project = consumer(tmp_path)
    root = tmp_path / 'catalog'
    remote = tmp_path / 'remote'
    put(root, 'profiles/main.toml', 'traits=["@builtin/a", "@builtin/b"]\nskills=["first/*", "second/*"]\n'
        '[[source]]\nid="first"\nprovider="git"\norigin="https://example.test/first"\nreference="main"\n'
        '[[source]]\nid="second"\nprovider="git"\norigin="https://example.test/second"\nreference="main"')
    put(root, 'traits/a.toml', 'hooks=["sessionStart"]\nbody="Use <skill:known> and <skill:unknown>."')
    put(root, 'traits/b.toml', 'hooks=["sessionStart"]\nbody="Again <skill:unknown>."')
    put(remote, 'known/SKILL.md', '---\nname: known\n---\n')
    put(remote, 'known/pspec.toml', 'version=2\nentry="SKILL.md"')
    clock = [0.0]
    calls = []
    monkeypatch.setattr(references, 'monotonic', lambda: clock[0])
    def lookup(source, recipe, *, deadline):
        calls.append((source, deadline))
        clock[0] = deadline
        return remote
    diagnostics = []
    output = dispatch(logical_event='sessionStart', agent='codex', cwd=project,
                      catalog=Catalog(builtin=root, git_resolver=lookup), diagnostics=diagnostics)
    assert calls == [('first', 1.0)]
    assert len(diagnostics) == 1 and 'budget exhausted' in diagnostics[0]
    assert 'Skills requiring dynamic resolution: known\n' in output
    assert output.count('Skill metadata unavailable: unknown') == 2


def consumer(tmp_path, config='profile="@builtin/main"\n'):
    project = tmp_path / "project"
    project.mkdir(parents=True)
    subprocess.run(["git", "init", "--quiet", str(project)], check=True)
    put(project, "openspec/.pspec/config.toml", config)
    return project


def catalog(tmp_path, trait='hooks=["sessionStart", "afterCompaction"]\nbody="guide"'):
    root = tmp_path / "catalog"
    put(root, "profiles/main.toml", 'traits=["@builtin/guide"]\n')
    put(root, "traits/guide.toml", trait)
    return root, Catalog(builtin=root)


def test_logical_selectors_expand_before_per_trait_native_exclusions():
    selected = selected_callbacks([
        "sessionStart", "afterCompaction", "~claude:SessionStart",
    ])
    assert {(item.agent, item.logical_event) for item in selected} == {
        ("codex", "sessionStart"), ("codex", "afterCompaction"),
    }
    direct = selected_callbacks(["claude:SessionStart"])
    assert {item.logical_event for item in direct} == {"sessionStart", "afterCompaction"}
    with pytest.raises(ConfigurationError, match="unsupported hook selector"):
        selected_callbacks(["~claude:PostCompact"])


def test_one_trait_exclusion_does_not_suppress_other_traits_or_callbacks(tmp_path):
    root = tmp_path / "catalog"
    put(root, "profiles/main.toml", 'traits=["@builtin/a", "@builtin/b"]\n')
    put(root, "traits/a.toml", 'hooks=["sessionStart", "~codex:SessionStart"]\nbody="a"')
    put(root, "traits/b.toml", 'hooks=["sessionStart", "afterCompaction"]\nbody="b"')
    bundle = compose(Catalog(builtin=root), "@builtin/main", agent="codex")
    start = callback_for("codex", "sessionStart")
    compact = callback_for("codex", "afterCompaction")
    assert matching_traits(bundle.traits, start) == ("@builtin/b",)
    assert matching_traits(bundle.traits, compact) == ("@builtin/b",)


def test_dispatch_uses_invocation_cwd_nearest_consumer_and_current_values(tmp_path):
    project = consumer(tmp_path)
    nested = project / "src/package"
    nested.mkdir(parents=True)
    root, configured = catalog(
        tmp_path,
        'hooks=["sessionStart", "afterCompaction"]\nbody="mode=<mode>"\n',
    )
    # Runtime traits do not declare compile-time interpolation, so values stay
    # data for conditions rather than becoming executable text templates.
    put(project, "openspec/.pspec/current.toml", '[vars]\nmode="first"\n')
    assert dispatch(logical_event="sessionStart", agent="codex",
                    cwd=nested, catalog=configured) == "mode=<mode>"
    put(root, "traits/guide.toml", 'hooks=["sessionStart"]\nbody="fresh"\nwhen="vars[\'mode\'] == \'second\'"')
    configured = Catalog(builtin=root)
    assert dispatch(logical_event="sessionStart", agent="codex",
                    cwd=nested, catalog=configured) is None
    put(project, "openspec/.pspec/current.toml", '[vars]\nmode="second"\n')
    assert dispatch(logical_event="sessionStart", agent="codex",
                    cwd=nested, catalog=configured) == "fresh"

    command = [sys.executable, "-c",
               "import json, pathlib; print(json.dumps({'name': pathlib.Path.cwd().name}))"]
    expression = f"run_json({command!r}).get('name') == 'package'"
    put(root, "traits/guide.toml",
        'hooks=["sessionStart"]\nbody="nested cwd"\nwhen=' + json.dumps(expression))
    assert dispatch(logical_event="sessionStart", agent="codex",
                    cwd=nested, catalog=Catalog(builtin=root)) == "nested cwd"
    assert dispatch(logical_event="sessionStart", agent="codex",
                    cwd=project, catalog=Catalog(builtin=root)) is None


def test_dispatch_uses_explicit_change_only_and_worktree_boundary(tmp_path):
    project = consumer(tmp_path)
    put(project, "openspec/.pspec/current.toml", '''
[vars]
mode="global"
[_change.selected]
mode="change"
''')
    root, _ = catalog(
        tmp_path,
        'hooks=["sessionStart"]\nbody="selected"\nwhen="vars[\'mode\'] == \'change\'"',
    )
    put(root, "profiles/main.toml", 'traits=["@builtin/guide"]\n[vars]\nmode="global"\n')
    configured = Catalog(builtin=root)
    assert dispatch(logical_event="sessionStart", agent="codex",
                    cwd=project, catalog=configured) is None
    assert dispatch(logical_event="sessionStart", agent="codex",
                    cwd=project, catalog=configured,
                    change="selected") == "selected"

    worktree = tmp_path / "worktree"
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "commit", "--allow-empty", "-qm", "initial"], cwd=project, check=True)
    subprocess.run(["git", "worktree", "add", "--detach", str(worktree)],
                   cwd=project, check=True, capture_output=True)
    put(worktree, "openspec/.pspec/config.toml", 'profile="@builtin/main"\n')
    assert dispatch(logical_event="sessionStart", agent="codex",
                    cwd=worktree, catalog=configured) is None


def test_dispatch_restores_after_compaction_through_context_capable_session_start(tmp_path):
    project = consumer(tmp_path)
    _, configured = catalog(tmp_path)
    guidance = dispatch(logical_event="afterCompaction", agent="claude",
                        cwd=project, catalog=configured)
    assert guidance == "guide"
    result = json.loads(serialize("claude", "afterCompaction", guidance))
    assert result == {"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": "guide",
    }}


def test_no_consumer_or_no_match_is_silent_and_does_not_evaluate_condition(tmp_path):
    root, configured = catalog(
        tmp_path, 'hooks=["afterCompaction"]\nbody="never"\nwhen="missing()"',
    )
    repo = tmp_path / "empty"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", str(repo)], check=True)
    assert dispatch(logical_event="sessionStart", agent="codex",
                    cwd=repo, catalog=configured) is None
    project = consumer(tmp_path / "with-consumer")
    assert dispatch(logical_event="sessionStart", agent="codex",
                    cwd=project, catalog=configured) is None


def test_eligible_condition_failure_returns_no_successful_partial_guidance(tmp_path):
    project = consumer(tmp_path)
    root = tmp_path / "catalog"
    put(root, "profiles/main.toml", 'traits=["@builtin/good", "@builtin/bad"]\n')
    put(root, "traits/good.toml", 'hooks=["sessionStart"]\nbody="good"')
    put(root, "traits/bad.toml", 'hooks=["sessionStart"]\nbody="bad"\nwhen="missing()"')
    result = None
    with pytest.raises(ConfigurationError, match="bad.toml"):
        result = dispatch(logical_event="sessionStart", agent="codex",
                          cwd=project, catalog=Catalog(builtin=root))
    assert result is None


@pytest.mark.parametrize("kind", ["timeout", "exit", "json", "object"])
def test_operational_probe_failure_omits_only_owning_trait(kind, tmp_path, monkeypatch):
    from powerspec.utils.processes import ProcessJSONError
    import powerspec.conditions as conditions

    project = consumer(tmp_path)
    root = tmp_path / "catalog"
    put(root, "profiles/main.toml",
        'traits=["@builtin/bootstrap", "@builtin/zmem", "@builtin/adhd"]\n')
    put(root, "traits/bootstrap.toml", 'hooks=["sessionStart"]\nbody="bootstrap"')
    put(root, "traits/zmem.toml",
        'hooks=["sessionStart"]\nbody="zmem"\n'
        'when="run_json([\'zmem\', \'service\', \'doctor\']).get(\'ok\') is True"')
    put(root, "traits/adhd.toml", 'hooks=["sessionStart"]\nbody="adhd"')
    seen = []
    def probe(argv, **options):
        seen.append((argv, options))
        raise ProcessJSONError(kind, f"controlled {kind}")
    monkeypatch.setattr(conditions, "run_json_object", probe)
    diagnostics = []

    result = dispatch(logical_event="sessionStart", agent="codex",
                      cwd=project, catalog=Catalog(builtin=root),
                      diagnostics=diagnostics)

    assert result == "bootstrap\n\nadhd"
    assert len(diagnostics) == 1
    assert "zmem.toml" in diagnostics[0] and f"controlled {kind}" in diagnostics[0]
    assert seen[0][1]["timeout"] == 2


def test_malformed_nearest_consumer_is_diagnostic_without_parent_fallback(tmp_path):
    project = consumer(tmp_path)
    nested = project / "child"
    put(nested, "openspec/.pspec/config.toml", "profile=12\n")
    _, configured = catalog(tmp_path)
    with pytest.raises(ConfigurationError, match="config.toml"):
        dispatch(logical_event="sessionStart", agent="codex",
                 cwd=nested, catalog=configured)


def test_native_documents_use_verified_context_delivery_callback():
    codex = native_document("codex")["hooks"]["SessionStart"]
    claude = native_document("claude")["hooks"]["SessionStart"]
    assert [entry["matcher"] for entry in codex] == ["startup|clear", "compact"]
    assert [entry["matcher"] for entry in claude] == ["startup|clear|fork", "compact"]
    assert "PostCompact" not in json.dumps({"codex": codex, "claude": claude})
    assert set(native_document("codex")["hooks"]) == {"SessionStart"}
    assert set(native_document("claude")["hooks"]) == {"SessionStart"}
    handlers = [entry["hooks"][0] for entry in (*codex, *claude)]
    assert all("pspec resolve hook" in handler["command"] for handler in handlers)
    assert all(handler["timeout"] == 5 for handler in handlers)
    assert all(handler["statusMessage"] for handler in handlers)
    assert all("resume" not in entry["matcher"] for entry in (*codex, *claude))
    forbidden = {
        "UserPromptSubmit", "PreToolUse", "PostToolUse", "PermissionRequest",
        "Stop", "SubagentStart", "SubagentStop", "SessionEnd",
    }
    assert forbidden.isdisjoint(native_document("codex")["hooks"])
    assert forbidden.isdisjoint(native_document("claude")["hooks"])


@pytest.mark.parametrize("agent", ["codex", "claude"])
@pytest.mark.parametrize("source", ["startup", "clear", "fork", "compact", "resume"])
def test_native_matchers_select_only_intended_commands(agent, source):
    entries = native_document(agent)["hooks"]["SessionStart"]
    commands = [item["hooks"][0]["command"] for item in entries
                if re.search(item["matcher"], source)]
    if source == "resume" or (source == "fork" and agent == "codex"):
        assert commands == []
    else:
        event = "afterCompaction" if source == "compact" else "sessionStart"
        assert commands == [f"pspec resolve hook {event} --agent {agent}"]


@pytest.mark.parametrize(("agent", "settings"), [
    ("codex", ".codex/hooks.json"),
    ("claude", ".claude/settings.json"),
])
def test_hook_provisioning_preserves_unrelated_settings_and_reuses(agent, settings, tmp_path):
    home, registry = tmp_path / "home", tmp_path / "registry"
    native = home / settings
    put(home, settings, '{"unrelated": {"keep": true}}\n')
    first = provision_hooks(agent, home=home, registry=registry)
    second = provision_hooks(agent, home=home, registry=registry)
    assert first.status == "installed" and second.status == "reused"
    document = json.loads(native.read_text(encoding="utf-8"))
    assert document["unrelated"] == {"keep": True}
    assert len(document["hooks"]["SessionStart"]) == 2


def test_hook_provisioning_updates_safely_owned_legacy_dispatchers(tmp_path, monkeypatch):
    import powerspec.provisioning as provisioning

    home, registry = tmp_path / "home", tmp_path / "registry"
    current = native_document("codex")
    legacy = deepcopy(current)
    legacy_entries = legacy["hooks"]["SessionStart"]
    legacy_entries[0]["matcher"] = "startup|resume|clear"
    for entry in legacy_entries:
        handler = entry["hooks"][0]
        handler["command"] = handler["command"].replace("pspec ", "powerspec ")
        handler.pop("timeout")
        handler.pop("statusMessage")

    monkeypatch.setattr(provisioning, "native_document", lambda _agent: legacy)
    assert provision_hooks("codex", home=home, registry=registry).status == "installed"
    monkeypatch.setattr(provisioning, "native_document", lambda _agent: current)
    assert provision_hooks("codex", home=home, registry=registry).status == "updated"
    assert provision_hooks("codex", home=home, registry=registry).status == "reused"

    installed = json.loads((home / ".codex/hooks.json").read_text(encoding="utf-8"))
    assert installed["hooks"]["SessionStart"] == current["hooks"]["SessionStart"]


def test_unsupported_hook_host_is_reported_without_native_writes(tmp_path):
    outcome = provision_hooks("kimi", home=tmp_path / "home", registry=tmp_path / "registry")
    assert outcome.status == "unsupported" and not outcome.ok
    assert not (tmp_path / "home").exists()


def test_modified_owned_hook_is_reported_without_overwrite(tmp_path):
    home, registry = tmp_path / "home", tmp_path / "registry"
    first = provision_hooks("codex", home=home, registry=registry)
    assert first.ok
    native = home / ".codex/hooks.json"
    document = json.loads(native.read_text(encoding="utf-8"))
    document["hooks"]["SessionStart"][0]["hooks"][0]["command"] = "changed elsewhere"
    native.write_text(json.dumps(document), encoding="utf-8")
    changed = native.read_bytes()
    second = provision_hooks("codex", home=home, registry=registry)
    assert second.status == "failed" and not second.ok
    assert native.read_bytes() == changed


def test_hook_cli_emits_only_structured_guidance_without_input(tmp_path, monkeypatch):
    from powerspec.cli import app
    import powerspec.cli.hook as cli
    project = consumer(tmp_path)
    root, _ = catalog(tmp_path)
    from contextlib import contextmanager
    @contextmanager
    def resources():
        yield root
    source_modes = []

    class Sources:
        def __init__(self, *, manage_binary):
            source_modes.append(manage_binary)

        def lookup(self, *_args, **_kwargs):
            raise AssertionError("local hook fixture performed remote lookup")

    monkeypatch.setattr(cli, "builtin_catalog_root", resources)
    monkeypatch.setattr(cli, "SaucepanSources", Sources)
    monkeypatch.chdir(project)
    result = CliRunner().invoke(
        app, ["resolve", "hook", "sessionStart", "--agent", "codex"],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"] == "guide"
    assert source_modes == [False]

import json
import subprocess

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


def payload(cwd, source="startup", event="SessionStart"):
    return {"session_id": "test", "cwd": str(cwd.resolve()),
            "hook_event_name": event, "source": source}


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


def test_dispatch_uses_event_cwd_nearest_consumer_and_current_values(tmp_path):
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
                    payload=payload(nested), catalog=configured) == "mode=<mode>"
    put(root, "traits/guide.toml", 'hooks=["sessionStart"]\nbody="fresh"\nwhen="vars[\'mode\'] == \'second\'"')
    configured = Catalog(builtin=root)
    assert dispatch(logical_event="sessionStart", agent="codex",
                    payload=payload(nested), catalog=configured) is None
    put(project, "openspec/.pspec/current.toml", '[vars]\nmode="second"\n')
    assert dispatch(logical_event="sessionStart", agent="codex",
                    payload=payload(nested), catalog=configured) == "fresh"


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
                    payload=payload(project), catalog=configured) is None
    assert dispatch(logical_event="sessionStart", agent="codex",
                    payload=payload(project), catalog=configured,
                    change="selected") == "selected"

    worktree = tmp_path / "worktree"
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "commit", "--allow-empty", "-qm", "initial"], cwd=project, check=True)
    subprocess.run(["git", "worktree", "add", "--detach", str(worktree)],
                   cwd=project, check=True, capture_output=True)
    put(worktree, "openspec/.pspec/config.toml", 'profile="@builtin/main"\n')
    assert dispatch(logical_event="sessionStart", agent="codex",
                    payload=payload(worktree), catalog=configured) is None


def test_dispatch_restores_after_compaction_through_context_capable_session_start(tmp_path):
    project = consumer(tmp_path)
    _, configured = catalog(tmp_path)
    guidance = dispatch(logical_event="afterCompaction", agent="claude",
                        payload=payload(project, source="compact"), catalog=configured)
    assert guidance == "guide"
    result = json.loads(serialize("claude", "afterCompaction", guidance))
    assert result == {"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": "guide",
    }}
    with pytest.raises(ConfigurationError, match="does not match"):
        dispatch(logical_event="afterCompaction", agent="claude",
                 payload=payload(project, source="startup"), catalog=configured)


def test_no_consumer_or_no_match_is_silent_and_does_not_evaluate_condition(tmp_path):
    root, configured = catalog(
        tmp_path, 'hooks=["afterCompaction"]\nbody="never"\nwhen="missing()"',
    )
    repo = tmp_path / "empty"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", str(repo)], check=True)
    assert dispatch(logical_event="sessionStart", agent="codex",
                    payload=payload(repo), catalog=configured) is None
    project = consumer(tmp_path / "with-consumer")
    assert dispatch(logical_event="sessionStart", agent="codex",
                    payload=payload(project), catalog=configured) is None


def test_eligible_condition_failure_returns_no_successful_partial_guidance(tmp_path):
    project = consumer(tmp_path)
    root = tmp_path / "catalog"
    put(root, "profiles/main.toml", 'traits=["@builtin/good", "@builtin/bad"]\n')
    put(root, "traits/good.toml", 'hooks=["sessionStart"]\nbody="good"')
    put(root, "traits/bad.toml", 'hooks=["sessionStart"]\nbody="bad"\nwhen="missing()"')
    result = None
    with pytest.raises(ConfigurationError, match="bad.toml"):
        result = dispatch(logical_event="sessionStart", agent="codex",
                          payload=payload(project), catalog=Catalog(builtin=root))
    assert result is None


def test_malformed_nearest_consumer_is_diagnostic_without_parent_fallback(tmp_path):
    project = consumer(tmp_path)
    nested = project / "child"
    put(nested, "openspec/.pspec/config.toml", "profile=12\n")
    _, configured = catalog(tmp_path)
    with pytest.raises(ConfigurationError, match="config.toml"):
        dispatch(logical_event="sessionStart", agent="codex",
                 payload=payload(nested), catalog=configured)


def test_native_documents_use_verified_context_delivery_callback():
    codex = native_document("codex")["hooks"]["SessionStart"]
    claude = native_document("claude")["hooks"]["SessionStart"]
    assert [entry["matcher"] for entry in codex] == ["startup|resume|clear", "compact"]
    assert [entry["matcher"] for entry in claude] == ["startup|resume|clear|fork", "compact"]
    assert "PostCompact" not in json.dumps({"codex": codex, "claude": claude})
    assert all("pspec resolve hook" in entry["hooks"][0]["command"] for entry in (*codex, *claude))


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


def test_hook_cli_reads_native_payload_and_emits_only_structured_guidance(tmp_path, monkeypatch):
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
        input=json.dumps(payload(project)),
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"] == "guide"
    assert source_modes == [False]

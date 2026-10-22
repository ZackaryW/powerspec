"""Exercise Powerspec's policy with the pinned ZuAT public lifecycle."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

import powerspec.provisioning as provisioning
from powerspec.hooks import native_document


@pytest.fixture(params=[("codex", ".codex/hooks.json"), ("claude", ".claude/settings.json")])
def hooks(tmp_path, request):
    agent, settings = request.param
    home, registry = tmp_path / "home", tmp_path / "registry"
    native = home / settings
    native.parent.mkdir(parents=True)
    native.write_text('{"unrelated": true}\n', encoding="utf-8")
    return SimpleNamespace(agent=agent, home=home, registry=registry, native=native)


def provision(hooks, **kwargs):
    return provisioning.provision_hooks(
        hooks.agent, home=hooks.home, registry=hooks.registry, **kwargs,
    )


def write_hooks(hooks, document):
    hooks.native.write_text(json.dumps({"unrelated": True, **document}, indent=3) + "\n",
                            encoding="utf-8")


def snapshot(hooks):
    return hooks.native.read_bytes(), hooks.native.stat().st_mtime_ns


def test_adopts_exact_unowned_hooks_without_native_changes(hooks):
    write_hooks(hooks, native_document(hooks.agent))
    before = snapshot(hooks)
    adopted = provision(hooks)
    assert adopted.ok and adopted.status == "reused", adopted.diagnostics
    assert adopted.operation_id
    assert snapshot(hooks) == before
    assert provision(hooks).status == "reused"
    assert snapshot(hooks) == before


def test_unowned_legacy_hooks_do_not_append_duplicates(hooks):
    legacy = native_document(hooks.agent)
    legacy["hooks"]["SessionStart"][0]["matcher"] = "startup|resume|clear"
    write_hooks(hooks, legacy)
    before = snapshot(hooks)
    result = provision(hooks)
    assert not result.ok and result.diagnostics
    assert snapshot(hooks) == before


def test_explicit_repair_reconciles_receipt_only_and_reuses(hooks, monkeypatch):
    current = native_document(hooks.agent)
    legacy = deepcopy(current)
    legacy["hooks"]["SessionStart"][0]["matcher"] = "startup|resume|clear"
    with monkeypatch.context() as patch:
        patch.setattr(provisioning, "native_document", lambda _: legacy)
        assert provision(hooks).ok
    write_hooks(hooks, current)  # External update leaves the valid receipt stale.
    before = snapshot(hooks)
    denied = provision(hooks)
    assert not denied.ok and "--repair-hooks" in " ".join(denied.diagnostics)
    assert snapshot(hooks) == before
    repaired = provision(hooks, repair_hooks=True)
    assert repaired.ok and repaired.status == "updated", repaired.diagnostics
    assert repaired.operation_id
    assert "ownership" in " ".join(repaired.diagnostics)
    assert snapshot(hooks) == before
    assert provision(hooks).status == "reused"
    assert snapshot(hooks) == before


@pytest.mark.parametrize("mutation", ["duplicate", "edited", "reordered"])
def test_repair_cannot_overwrite_ambiguous_or_edited_hooks(hooks, mutation):
    assert provision(hooks).ok
    document = json.loads(hooks.native.read_text(encoding="utf-8"))
    entries = document["hooks"]["SessionStart"]
    if mutation == "duplicate":
        entries.append(deepcopy(entries[0]))
    elif mutation == "reordered":
        entries.reverse()
    else:
        entries[0]["hooks"][0]["command"] = "user-edited-command"
    write_hooks(hooks, document)
    before = snapshot(hooks)
    rejected = provision(hooks, repair_hooks=True)
    assert not rejected.ok and rejected.diagnostics
    assert snapshot(hooks) == before


def test_unrelated_insertions_preserve_owned_identity(hooks):
    assert provision(hooks).ok
    document = json.loads(hooks.native.read_text(encoding="utf-8"))
    document["hooks"]["SessionStart"].insert(0, {
        "matcher": "foreign", "hooks": [{"type": "command", "command": "foreign"}],
    })
    write_hooks(hooks, document)
    before = snapshot(hooks)
    assert provision(hooks).status == "reused"
    assert snapshot(hooks) == before


def test_verified_absent_owned_hooks_can_be_reinstalled(hooks):
    assert provision(hooks).ok
    write_hooks(hooks, {"hooks": {}})
    result = provision(hooks)
    assert result.ok and result.status == "installed", result.diagnostics
    assert provision(hooks).status == "reused"


@pytest.mark.parametrize("classification", ["absent", "current", "outdated", "unowned", "conflict", "indeterminate", "unsupported"])
def test_partial_inspection_never_authorizes_a_mutation(tmp_path, monkeypatch, classification):
    observed = SimpleNamespace(classification=classification, completeness="partial",
                               diagnostics=("provider unresolved",), owned=True, source_matches=True)
    monkeypatch.setattr(provisioning, "inspect_asset", lambda *a, **kw: observed)
    def unexpected(*args, **kwargs):
        pytest.fail("incomplete inspection authorized mutation")
    monkeypatch.setattr(provisioning, "install", unexpected)
    monkeypatch.setattr(provisioning, "update_asset", unexpected)
    result = provisioning.provision_hooks("codex", home=tmp_path, repair_hooks=True)
    assert not result.ok and "provider unresolved" in result.diagnostics


def test_failed_provider_repair_preserves_diagnostics_and_recovery_id(tmp_path, monkeypatch):
    observed = SimpleNamespace(classification="conflict", completeness="complete",
                               diagnostics=(), owned=True, source_matches=True)
    monkeypatch.setattr(provisioning, "inspect_asset", lambda *a, **kw: observed)
    def fail(asset, **context):
        assert context["force"] is True
        assert context["receipt_only"] is True
        return SimpleNamespace(ok=False, status="partial", diagnostics=("publication failed",),
                               operation_id="recover-this-operation")
    monkeypatch.setattr(provisioning, "update_asset", fail)
    result = provisioning.provision_hooks("codex", home=tmp_path, repair_hooks=True)
    assert not result.ok and result.operation_id == "recover-this-operation"
    assert result.diagnostics == ("publication failed",)


def test_receipt_repair_cannot_replace_concurrent_baseline_restoration(hooks, monkeypatch):
    current = native_document(hooks.agent)
    legacy = deepcopy(current)
    legacy["hooks"]["SessionStart"][0]["matcher"] = "startup|resume|clear"
    with monkeypatch.context() as patch:
        patch.setattr(provisioning, "native_document", lambda _: legacy)
        assert provision(hooks).ok
    write_hooks(hooks, current)
    inspect = provisioning.inspect_asset
    restored = []
    def inspect_then_restore(*args, **kwargs):
        result = inspect(*args, **kwargs)
        assert result.classification == "conflict" and result.source_matches
        write_hooks(hooks, legacy)
        restored.append(snapshot(hooks))
        return result
    monkeypatch.setattr(provisioning, "inspect_asset", inspect_then_restore)
    result = provision(hooks, repair_hooks=True)
    assert not result.ok and "receipt-only" in " ".join(result.diagnostics)
    assert snapshot(hooks) == restored[0]

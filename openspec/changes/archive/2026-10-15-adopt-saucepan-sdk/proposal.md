# Proposal

## Why

Powerspec currently pins an old Saucepan Python SDK, accepts only the 0.5/0.6 executable lines and locates materializations through legacy app views and source history. The new SDK requires explicit UUID claims and returned output paths while Powerspec must retain its strict no-fetch lookup and safe upgrade behavior.

## What Changes

- Adopt manager 0.10 and SDK 0.2.0 profile contracts in a follow-on checkpoint: Rust expands `explicit-update`; Powerspec explicitly registers and adopts its flat policies, preserves upgrade-only updates, and retains expanded retry inputs.

- **BREAKING**: adopt the current Python `Client`, typed request/result contracts and structured errors; remove `Saucepan`, `shared_executable_path`, legacy view/history/token assumptions and diagnostic-string matching.
- Keep one stable Powerspec application, separate claims by explicit consumer scope, and retain profile aliases as Powerspec names rather than application identities.
- Keep sync, status, hooks and ordinary lookup read-only; ensure creates only missing intent and upgrade alone explicitly refreshes existing selections.
- Register flat immutable policies and durable pins for selected outputs; retain prior paths until replacement validation/provisioning and cleanup have completed.
- Preserve authored profile source syntax, catalog/skill path validation, ZuAT ownership, installed names and the existing all-success condition for obsolete-skill removal.
- Update executable discovery/provisioning for the tested 0.9 line while keeping the 24-hour Zuu check policy, explicit-client bypass and bounded read-only inspection.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `remote-sources`: scoped UUID SDK bindings, retained materializations and structured failure reconciliation while preserving lifecycle boundaries.
- `managed-saucepan-binary`: independently resolved executable, tested new protocol and packaged SDK compatibility.

## Impact

`src/powerspec/sources.py`, `saucepan_tool.py`, `doctoring.py`, workspace/status/upgrade/hook callers, dependency pin and lockfile, focused pytest integration/CLI tests and source documentation. Reuse Zuu's binary lifecycle, existing inspection helpers and the SDK transport; no new generic utility framework. No changes to authored profile syntax, packaged builtin build-source policy, native skills delivery, Saucepan storage, user credentials or remote repository state.

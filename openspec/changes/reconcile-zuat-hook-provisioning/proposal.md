# Proposal

## Why

Powerspec still uses an older ZuAT revision and falls back to hook installation when inspection is indeterminate, risking duplicate callbacks. ZuAT 0.1.2 now provides ownership-aware inspection and recoverable receipt repair that Powerspec must consume explicitly.

## What Changes

- Pin the published ZuAT 0.1.2 revision and refresh the lockfile.
- Reuse current owned hooks, update safely outdated hooks, adopt exact unowned groups, and install only after verified absence.
- Stop on incomplete or ambiguous hook inspection instead of attempting installation.
- Add `upgrade --repair-hooks` for valid owned receipts whose uniquely selected installed hooks already match the desired source; keep skill `--force` separate.
- Preserve provider diagnostics and recovery operation IDs and cover the real ZuAT integration in isolated fixtures.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `trait-hook-delivery`: Reconcile hook assets using complete ownership evidence and explicit receipt repair.
- `cli-product-surface`: Expose narrowly scoped hook repair during upgrade.

## Impact

Changes affect `provisioning.py`, `upgrading.py`, upgrade CLI handling, hook documentation, integration tests, `pyproject.toml`, and `uv.lock`. No live user hook files or ZuAT private receipts are edited directly. The unrelated skill-routing change remains separate.

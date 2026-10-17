# Proposal

## Why

PowerSpec publishes its manager into `~/.saucepan/bin` before initializing the shared store. Saucepan correctly refuses this nonempty root, leaving init incomplete while doctor reports a usable executable and upgrade requires the missing materialization.

## What Changes

- Bootstrap the default store using a validated manager staged outside that store, then publish the executable and its successful release-check record.
- Recover the narrowly recognized binary-only failed setup by preserving its installer files outside the store before initialization. Refuse automatic recovery of unknown data or linked paths.
- Keep existing store validation, explicit executable/client behavior, read-only operations, and missing-only init semantics.
- Clarify that doctor's executable check does not certify selected source materializations; document rerunning init before upgrade after incomplete setup.
- Verify actual manager initialization and source acquisition in isolated homes, including recovery and retries.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `managed-saucepan-binary`: Order default installation around store initialization and preserve failed bootstrap assets.
- `cli-product-surface`: Clarify diagnostic limits and safe first-use recovery.

## Impact

PowerSpec's `saucepan_tool.py`, source integration tests, doctor output, and remote-source instructions. No Rust schema changes, legacy-store migration, new service, automatic upgrade fallback, or dependency changes. Active change artifacts remain outside incremental commits; no remote pushes.

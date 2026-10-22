# Proposal

## Why

Powerspec currently extracts and replaces the raw Saucepan manager at `~/.saucepan/bin/saucepan`, a path Saucepan's managed installation uses for an owned shim. Adopting Saucepan's official setup contract removes competing ownership while preserving automatic authorized first-use setup and read-only lookup.

## What Changes

- Consume Saucepan's new public setup/status contract instead of publishing a raw executable through Zuu at the shared launcher path.
- Use a verified, explicitly pinned official installer for missing installations. Keep dependency staging separate from Saucepan's store and delegate root initialization, policies, bootstrap and receipts to Saucepan.
- Reuse compatible managed installations without an implicit shared update. Surface incompatibility and explicit Saucepan self-update guidance; `pspec upgrade` continues to refresh selected resources without silently changing the shared manager.
- Preserve standalone executable overrides and injected SDK clients. Report executable compatibility separately from managed ownership and source readiness.
- Direct existing raw-manager installations to Saucepan's explicitly selected, verified backup/migration flow; never infer migration permission from init, upgrade, filename, or the old release-check cache.
- Update the immutable SDK dependency and supported CLI contract only after the provider implementation and acceptance evidence exist.
- **BREAKING:** the default shared installation will no longer be directly installed or refreshed by Powerspec's Zuu manager. An unmanaged default-path executable requires explicit migration or an explicit standalone override.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `managed-saucepan-binary`: Saucepan-owned installation, explicit dependency staging, compatibility/reuse, standalone overrides and migration handoff.
- `cli-product-surface`: First-use setup and upgrade ownership boundaries; doctor distinguishes compatible binaries from verified managed installation.

## Impact

Baseline: Powerspec `f97b955`. Affects `saucepan_tool.py`, `saucepan_bootstrap.py`, source-client construction, doctor, installation/upgrade presentation, dependency pins, tests and documentation. No changes to resource receipts, source retention, native agent asset ownership, or global skill copies are intended.

Provider dependency: `../../../../../saucepan/openspec/changes/archive/2026-10-21-add-managed-setup/` from this directory. Implement and verify that contract first. This change is separate from `add-pspec-skill-routing`; reconcile overlapping source/lifecycle tests when both land, without changing its scope or checking its tasks complete. These artifacts authorize planning, not host migration, release publication or implementation.

# Proposal

## Why

`current.toml` is the gitignored temporal variable surface, but Powerspec cannot
clear it. Archived changes can therefore leave stale runtime answers active in
later sessions, and `pspec flush` still reports a placeholder error.

## What Changes

- Implement `pspec flush` and `powerspec flush` against the nearest Git-bounded consumer.
- Clear one explicit `[_change.<name>]` layer while preserving shared and other change state.
- Clear all temporal state when no change is supplied, leaving an empty `[vars]` table.
- Make missing/already-cleared state idempotent and use validated atomic replacement.
- Publish and document a global post-success archive handoff plus the persistent-versus-temporal boundary.

## Capabilities

### New Capabilities

- `temporary-state-cleanup`: Safe, scoped, idempotent cleanup of gitignored runtime variables.

### Modified Capabilities

None.

## Impact

Adds a small TOML round-trip dependency, a temporal-state service, CLI behavior,
tests, one global compile-time archive context, and lifecycle documentation.
Persistent `config.toml`, profiles, skills, hooks, and agent installations are
outside the cleanup mutation boundary; normal sync owns publication to `config.yaml`.

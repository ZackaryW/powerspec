## Why

A fresh machine cannot run the advertised init/sync flow: init only scaffolds files, sync requires pre-existing remote materializations, and Saucepan's native missing-secret error is not recognized as a possible first use. The separate install command introduced a setup step the intended lifecycle did not include.

## What Changes

- Restore agent provisioning to `pspec init --agent <agent>` with profile-declared skill scopes and user-level hooks. Plain init remains valid without guessing an agent, but prepares selected sources.
- Let sync acquire missing selected sources while preserving already materialized revisions; upgrade remains the explicit refresh and removal operation.
- Handle both missing native secrets and missing indexes through Saucepan's guarded initialization API; never reset existing store data or credentials.
- **BREAKING**: remove `pspec install` and update help, bundled bootstrap guidance, and documentation to direct users to init.
- Preserve completed setup effects after failure and support repeat init/sync on existing consumers.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli-product-surface`: replace the separate install lifecycle with init provisioning and missing-source acquisition during sync.
- `context-sync`: permit first acquisition without refreshing current materializations or provisioning agents.
- `user-skill-installation`: clarify optional agent selection and resumable initialization boundaries.

## Impact

CLI init/sync/composition, Saucepan first-use handling, existing ZuAT provisioning orchestration, tests, and current user documentation. No new dependencies or generic utilities are needed. Existing archived change artifacts remain historical records. The prior missing-secret fix and regression tests are included in this change.

# Proposal

## Why

Powerspec still acquires memory skills from the predecessor zmem repository while its installed skills expect the TypeScript/Node engine. This machine's `zmem` command selects the Python predecessor, so memory queries and commit validation cannot use the intended contract.

## What Changes

- Acquire the bundled memory profile's skills from `https://github.com/ZackaryW/zmem2`, retaining the `zmem` alias, `main` reference, profile identity, scopes and three native skill names.
- Clarify the shared standing guidance and documentation: the intended runtime is the zmem2 Node CLI, identified by executable location and command surface, not the shared command name alone.
- Document and verify existing-consumer migration through source initialization before lookup-first upgrade, preserving ownership checks and legacy source retention.
- Switch this authorized machine to a verified zmem2 package, preserve predecessor data and rollback evidence, initialize Powerspec's computed memory and verify queries and commit checks.
- Keep runtime installation an explicit environment action; ordinary Powerspec initialization will not become a general tool installer.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `profile-skill-bundles`: define the zmem2 source with stable memory-skill identities and guidance identifying the required runtime without gating delivery on a service probe.

## Impact

Changes are limited to bundled profile/guidance resources, focused integration tests, documentation, this change's artifacts and the authorized local environment. Existing source acquisition, ZuAT ownership and hook contracts are reused. No Python dependency, provider API, global hook format or generic installer is introduced. Predecessor databases and extensions remain untouched; no publication or push is authorized.

# Proposal

## Why

Working resolution still needs complete, portable skill resources and repeatable installation. Ship bundled resources and initialize a repository without downloading OpenSpec on every setup or creating unwanted repository-level skills.

## What Changes

- Switch package resource builds to Hatchling while retaining uv and uv run pytest.
- Vendor a pinned compatible snapshot of selected committed OpenSpec skills with license and provenance; package complete authored and upstream resources in wheel and sdist.
- Plan and provision selected skills through ZuAT for one explicit agent, preserving each contributing profile's user/project scope.
- Implement Git-root pspec init with upstream local skill generation disabled, persistent configuration preserved, and current.toml ignored.
- Reuse matching installations and report conflicts and partial failures without automatic rollback or shared-skill removal.

## Capabilities

### New Capabilities

- `user-skill-installation`: Complete bundled resources, scoped provisioning, native availability boundaries, and repeatable initialization.

### Modified Capabilities

None. This change uses the incremental CLI contract established by implement-skill-content-resolution.

## Impact

Depends on establish-profile-consumer-resolution and implement-skill-content-resolution. Changes packaging metadata, resource layout, the installation adapter, and src/powerspec/cli/init.py. Maintainer preparation may fetch upstream; normal build and init use local packaged resources.

Completion means an installed distribution initializes disposable repositories and agent homes with complete resources, including a verified offline wheel rebuilt from sdist. Hook registration is delivered by implement-trait-hook-delivery; user-added remote sources, full sync, and flush remain separate.

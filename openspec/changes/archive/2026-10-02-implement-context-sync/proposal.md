# Proposal

## Why

Static project guidance and runtime conditions have been conflated as two trait modes. The revised foundation separates contexts from traits, but sync remains a placeholder and cannot publish the selected compile-time contexts into OpenSpec configuration.

## What Changes

- Implement `pspec sync` and its powerspec alias using the owning consumer, selected/global profile contexts, and persistent shared configuration.
- Compile context inputs, Python when conditions, variable substitutions, and skill references into destination-labelled guidance without runtime prompts or temporal/change overrides.
- Reconcile Powerspec-owned contributions in config.yaml using distinct provenance identifiers for every attachment, preserving user-owned content and removing obsolete managed contributions.
- Keep runtime traits, hook health checks, current.toml, and skill procedures outside compiled guidance. Context output remains a snapshot until the next sync.
- Preserve schema selection and existing OpenSpec destinations; no new utility artifact, dynamic dispatcher command, or skill execution is introduced.

## Capabilities

### New Capabilities

- `context-sync`: Compile selected context resources and reconcile their managed OpenSpec configuration contributions deterministically.

### Modified Capabilities

- `cli-scaffold`: Replace only sync's unavailable behavior with its capability contract while preserving help/import/syntax and remaining placeholder guarantees.

## Impact

Depends on establish-profile-consumer-resolution for distinct contexts/traits, profile composition, consumer discovery, persistent input layers, and the shared trusted Python-condition adapter. It can be implemented independently of hook delivery, installed skill resolution, remote acquisition, or packaging by injecting validated local catalogs. Packaged and acquired catalogs later feed the same boundary.

Implementation affects src/powerspec/cli/sync.py, a context compiler, YAML reconciliation, and CLI/integration fixtures. It may add a compatible YAML round-trip dependency; preserve uv and uv run pytest. This change does not install resources, register hooks, mutate source profiles, infer an active change, or implement flush.

Completion means a disposable consumer publishes the reviewed Python CLI and utility contexts, preserves custom YAML guidance, removes deselected contributions, and produces no changes on an identical second sync. Runtime-only service health continues to be evaluated by traits rather than published as a standing fact.

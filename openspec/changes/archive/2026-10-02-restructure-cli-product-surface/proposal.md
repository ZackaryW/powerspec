# Proposal

## Why

Powerspec's implemented commands expose working behavior, but the command surface still reflects implementation history: human workflows, agent protocols, state maintenance, source acquisition, skill installation, and hook reconciliation are mixed together. This makes common operations difficult to discover, gives `init` too many responsibilities, and leaves users without a read-only way to understand or diagnose a consumer before changing it.

## What Changes

- Reorganize the CLI around a human control plane: `init`, `status`, `sync`, `install`, `upgrade`, `doctor`, and `config`.
- Make `init` setup-only: it establishes the Git-bounded OpenSpec consumer and Powerspec configuration without acquiring sources, installing skills, or registering hooks.
- Add `install --agent` as the explicit operation that acquires missing configured sources and reconciles the selected skills and hooks for one agent installation scope.
- Group temporary-state operations under `state` and machine-facing protocols under `resolve`.
- Keep `skill`, `hook`, and `flush` as hidden compatibility aliases while callers migrate.
- Add read-only `status` and `doctor` commands, plus configuration inspection and profile selection commands.
- Give commands consistent structured application results and human or JSON presentation, with successful results on stdout and diagnostics on stderr.
- Make `sync` validate the complete effective bundle, including consumer-local resources, before atomically publishing generated OpenSpec guidance.

## Capabilities

### New Capabilities

- `cli-product-surface`: Defines the public command taxonomy, setup/install lifecycle, inspection and diagnosis operations, configuration and state groups, machine-facing resolution group, compatibility aliases, and presentation contracts.

### Modified Capabilities

- `cli-scaffold`: Replaces the historical placeholder-oriented command inventory with the implemented, grouped Powerspec command surface while retaining equivalent entrypoints and side-effect-free help and imports.

## Impact

- Refactors `src/powerspec/cli` into thin Typer adapters backed by shared application services and presenters.
- Changes `pspec init` so existing automation that relied on implicit skill or hook installation must call `pspec install --agent <agent>` explicitly.
- Adds commands without changing the `pspec` and `powerspec` executable names.
- Preserves the existing machine protocol temporarily through hidden aliases.
- Extends tests and documentation for the new lifecycle, output, and compatibility behavior.

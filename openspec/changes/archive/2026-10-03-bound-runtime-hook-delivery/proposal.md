# Proposal

## Why

Codex currently invokes Powerspec on native `resume`, which Codex Desktop may emit for ordinary submitted turns, and generated callbacks inherit a 600-second host timeout. Runtime probes and catalog resolution can therefore delay every prompt or leave the whole interaction waiting far longer than advisory guidance should permit.

## What Changes

- Restrict Powerspec context delivery to actual context-establishing boundaries: startup, clear, supported forks, and compaction restoration.
- Explicitly exclude native resume, prompt-submission, tool-use, permission, stop, subagent, and session-end callbacks from Powerspec provisioning.
- Add short native callback deadlines and visible status messages so guidance cannot indefinitely block the host.
- Keep runtime conditions fresh at each matched Powerspec boundary, including the existing Zmem service-doctor condition, without evaluating them on ordinary prompts.
- Isolate operational command-probe failures to their owning optional trait so unrelated bootstrap and accessibility guidance can still be delivered with a diagnostic.
- Reconcile prior Powerspec callback shapes without duplicating replacements, while preserving hook entries owned by other tools.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `trait-hook-delivery`: Narrow native lifecycle mappings, require bounded advisory callbacks, isolate operational probe failures, and migrate older owned registrations.
- `profile-skill-bundles`: Allow an evaluation boundary to impose a command-probe budget no greater than the shared default while preserving strict condition semantics.

## Impact

The change affects native callback definitions and serialization in `src/powerspec/hooks.py`, runtime condition evaluation in `src/powerspec/conditions.py`, ZuAT-based hook reconciliation in `src/powerspec/provisioning.py`, and their focused tests. Existing trait TOML, including the Zmem doctor condition and ADHD preference condition, remains authored in the same shape. User-owned and third-party hooks remain outside Powerspec ownership.

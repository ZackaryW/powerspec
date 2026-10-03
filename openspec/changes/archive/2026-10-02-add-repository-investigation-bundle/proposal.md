# Proposal

## Why

The old governance setup supplied repository investigation and prototype assessment separately. Migrate them as one global bundle so investigation gathers relevant evidence and only unresolved material feasibility questions lead to bounded experiments. Guidance also needs to recognize resources already selected by the consumer without confusing selection with installation or execution.

## What Changes

- Add a global repository-investigation profile combining a bounded investigation/feasibility skill with runtime reminders.
- Let the agent choose from usable investigation tools at skill invocation: prefer CodeGraph for broad system understanding and Ripwire for targeted changes. Use available alternatives or direct source inspection when needed; do not automatically install tools or create a CodeGraph index.
- Use the foundation's new armed(kind, reference) condition capability to include or omit guidance based on resources selected after composition and exclusions.
- Preserve the active decision policy and accepted answers; experiments require appropriate scope/authorization and never become mandatory for every task.
- Follow the migration sequence: context classification first, bootstrap delivery second, this combined bundle third. Source-only edits do not establish functioning delivery.

## Capabilities

### New Capabilities

- `repository-investigation`: One global bundle for bounded repository investigation and feasibility assessment, with agent-selected CodeGraph/Ripwire investigation and resource-aware runtime selection.

### Modified Capabilities

None. The in-flight profile-skill-bundles specification owns the shared armed checker and is revised there, without duplicating its contract here.

## Impact

Adds authored resources under .pspec/profiles, .pspec/traits, and .pspec/skills after the reviewed classification/bootstrap edits. Depends on establish-profile-consumer-resolution (including armed), implement-skill-content-resolution, bundle-resources-and-initialize, and implement-trait-hook-delivery. The foundation's checker is reused by both context sync and hooks. No new CLI command, source registry, automatic indexing, zmem replacement, or mandatory prototype artifact is introduced.

The bundle reuses the implemented profile composition, ordinary-skill
provisioning, and generic hook dispatcher. It adds no CLI command. Completion
requires fixture-based composition and delivery verification, not merely the
presence of these files.

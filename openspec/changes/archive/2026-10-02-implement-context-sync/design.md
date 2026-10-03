# Design

## Context

See proposal.md for motivation. The revised foundation separates .pspec/contexts from .pspec/traits and provides composition, persistent layers, and explicit Python-condition evaluation. The reviewed Python/utility resources now occupy contexts/ with updated profile references; foundation composition verification remains pending. sync.py is a Typer placeholder, and config.yaml is an unmanaged spec-driven scaffold. Existing CLI tests assume every domain command remains unavailable.

This milestone depends on the foundation only. Skill lookup, packaging, remote catalogs, and hook delivery independently consume the same resolved profile data. Existing canonical specs describe CLI scaffolding; context publication is a new capability.

## Goals / Non-Goals

**Goals:** Reconcile selected compile-time contexts into one owning OpenSpec configuration, preserve user content, and produce an idempotent published snapshot.

**Non-Goals:** Runtime trait dispatch, skill installation/execution, automatic archive cleanup, schema creation, statement/script execution, migration of skill-manifest guards, or an additional source-management command family.

## Decisions

### Keep composition, compilation, reconciliation, and publication separate

Obtain a resolved bundle from the foundation, then compile only its contexts. Compile each resource's persistent shared values and eligible attachment guards into destination-labelled contributions with resource provenance. Traits remain available to pspec hook; skills retain pspec skill resolution. Do not manufacture a generic resolve command or ^pspec entry in this static publication.

Validate complete inputs and references before publication. Substitute declared inputs once; resolve <skill:name> through the catalog's declared installed name without querying native installations or including procedures. Unsupported or conflicting input/reference shapes fail explicitly. Reuse already materialized source catalogs without refresh, installation, or installed-skill removal. Missing required resources fail without automatic acquisition; source unavailability never authorizes deletion of installed copies. Managed context removals in config.yaml remain normal reconciliation. The compiler can run against injected local fixture catalogs, so sync need not wait for packaging or production provisioning.

Alternative rejected: compiling static guidance and runtime instructions through one trait mode switch. It would recreate the boundary the context/trait split removes.

### Input timing follows resource ownership

Use config shared > selected profile > global profile > declaration default. No current.toml, _change tables, prompts, or automatic persistence enters compilation. Evaluate attachment when expressions through the shared case18 adapter with invocation environment/cwd/Git root and persistent context vars, which, and run_json. Bind armed to the effective bundle after composition/exclusions, before attachment conditions; queries do not inspect emitted guidance or installations. Results describe this compilation, not ongoing readiness. Mutable service health belongs to runtime traits; sync never evaluates their conditions. An explicitly authored context probe follows the shared trusted-capability contract. Require actual Boolean results; expression/probe errors fail compilation rather than mean false.

Alternative rejected: silently compiling temporal decisions because they happen to be present. Shared configuration must not drift with one agent session or active change.

### Ownership is represented in the generated YAML

Use stable caret identifiers such as ^@builtin/python-simple-cli/context/1 and ^@builtin/utility-plan/rules.design/1. The components are qualified resource, destination, and explicit attachment id or one-based ordinal at that destination. Validate escaping/uniqueness before rendering. Explicit IDs tolerate declaration reordering; ordinal fallback keeps existing authored resources usable. Every attachment remains distinct even when bodies coincide.

For scalar context text, retain user content outside a single managed region delimited by <!-- pspec:contexts:start --> and <!-- pspec:contexts:end -->. Put each generated body and its caret marker inside the region. For rules.<artifact> and operations.<operation>.guidance, use individual scalar list entries with matching pspec ownership comments and trailing caret identifiers. Reject duplicate/unbalanced markers and incompatible scalar/list types. Replace the managed region/entries from the complete new contribution set, including removals when conditions become false or selections change. Preserve user entries and their relative ordering. Append new managed list entries in deterministic composition/declaration order.

Use a YAML round-trip parser preserving unrelated comments and scalar values; pin and verify the chosen public dependency when implementing the reconciler. Do not rewrite all configuration from an ordinary dictionary. No sidecar manifest or synchronization database is added. If the rendered document has no semantic managed change, leave the original bytes untouched; repeated publication must also stabilize its formatting.

Alternative rejected: one identifier per context or an unmarked scalar append. Neither provides safe reconciliation for multiple attachments and obsolete output.

### Publication has one target and reports its actual result

Require an existing owning consumer and target config.yaml; initialization remains init's responsibility. Prepare the complete candidate, validate it, and replace the owning file through a same-directory staged write. A failure before replacement leaves the original intact; report publication errors without a success message and clean up request-owned staging files. Publication plumbing modifies no TOML, catalogs, current values, agent assets, or other consumers. Conditions are trusted rules and can invoke side-effecting methods/commands; staging protects publication against evaluation errors but cannot isolate or roll back callback effects. Use observational conditions and disposable capability fixtures.

Keep sync's existing no-argument syntax; add no speculative options. Both aliases report updated/unchanged with the target on success and nonzero diagnostics on failure. Help and import remain side-effect-free. Unimplemented domain commands remain honest placeholders according to their own readiness, rather than tests assuming all commands advance together.

## Risks / Trade-offs

- Compiled observations become stale -> document snapshot timing and keep mutable readiness conditions in runtime traits.
- Handwritten guidance could be mistaken for generated output -> delimit scalar ownership, label individual entries, and reject ambiguous markers before writes.
- YAML formatting could churn -> exercise comments/scalars and exact repeat-sync bytes through round-trip fixtures.
- Legacy external resources may still use traits -> report explicit migration diagnostics; the reviewed Python/utility sources have already moved to contexts/.

## Migration Plan

Implement context compilation and fixtures first, then YAML reconciliation and safe publication, then wire sync and incremental CLI readiness. Use the foundation-migrated Python and utility sources for an isolated end-to-end walkthrough. Preserve schema choice and manually authored data. Rolling back the package does not automatically erase previously published guidance; source configuration remains the authority for a subsequent compatible sync.

## Purpose

Publish compile-time context guidance into its owning OpenSpec configuration while preserving user content and keeping runtime traits and skill procedures independently resolved.

## ADDED Requirements

### Requirement: Sync selects only compile-time contexts

Both pspec sync and powerspec sync SHALL use the nearest owning consumer within the enclosing Git boundary, including nested consumers and worktrees, and select contexts contributed by its effective profiles. Profile exclusions and subprofile composition SHALL follow profile-skill-bundles. Runtime traits SHALL NOT be compiled, dispatched, or converted into commands in config.yaml. Sync SHALL reuse existing source materializations without refresh. Sync SHALL NOT install or remove skills, fetch sources, register hooks, execute procedures, or flush state. Missing required materialized resources SHALL produce diagnostics without repair; unavailable or removed sources SHALL NOT cause installed-skill deletion. This preservation SHALL NOT prevent normal reconciliation of obsolete managed context guidance. Missing consumers or missing/malformed target configuration SHALL produce diagnostics rather than guessed initialization.

#### Scenario: Python and utility contexts are selected
- **WHEN** a consumer selects the reviewed Python CLI profile containing the utility-planning subprofile
- **THEN** sync publishes the selected Python CLI and utility context attachments at their declared destinations without executing planning or TDD

#### Scenario: Runtime trait also selected
- **WHEN** the effective profile also selects a guarded runtime trait
- **THEN** sync leaves its body and runtime condition out of the generated configuration

#### Scenario: Nearest target is invalid
- **WHEN** the nearest consumer or its existing config.yaml is missing or malformed
- **THEN** sync reports the problem without selecting another consumer or creating guessed configuration

### Requirement: Context compilation uses noninteractive shared inputs

Context compilation SHALL use persistent config.toml shared variables, selected-profile defaults, global-profile defaults, then context declaration defaults. It SHALL NOT consume current.toml, change-specific values, or runtime prompts. Invalid explicit and missing required values SHALL produce diagnostics without fallback from invalid values. Declared variable placeholders SHALL be substituted once; unrelated angle-bracket prose SHALL remain literal. Skill references SHALL be rendered as their declared installed names from the validated catalog without requiring installation or embedding SKILL.md content. Unknown declared references SHALL fail rather than be silently omitted.

#### Scenario: Reviewed tooling defaults
- **WHEN** the Python CLI context compiles with the profile defaults and an explicit utility_path
- **THEN** its guidance identifies uv, pytest, uv run pytest, and the configured utility location without a prompt or tool installation

#### Scenario: Temporal override does not compile
- **WHEN** current.toml or a change table supplies another test_command
- **THEN** sync still uses shared persistent/default values and leaves those runtime files unchanged

#### Scenario: Skill reference is available as a resource
- **WHEN** an attachment references pspec-tdd from a validated catalog
- **THEN** its published guidance names that skill without reading or executing its procedure

#### Scenario: Broken temporal file does not affect compilation
- **WHEN** shared persistent context inputs are valid but current.toml contains malformed runtime state
- **THEN** sync compiles without reading that temporal file, preserving it for separate runtime diagnosis

### Requirement: Context conditions produce a compilation snapshot

Sync SHALL evaluate eligible attachment Python when expressions through the shared condition contract with invocation cwd/environment/Git root and persistent context vars. Temporal/change values SHALL NOT participate. Omission SHALL be unconditional; Boolean false SHALL omit only that attachment. Syntax/name/non-Boolean errors and capability/probe failures SHALL fail compilation without successful partial output. Results SHALL NOT be persisted as variable answers.

Published guidance SHALL remain a snapshot until another sync. Mutable runtime service readiness SHALL remain trait-owned without implicit re-evaluation from config.yaml. Conditions SHALL retain the trusted-rule contract without guarantees of sandboxing, complete execution-time limits, or rollback of callback effects.

#### Scenario: Persistent language controls guidance
- **WHEN** an attachment evaluates vars['language'] == 'python' with persistent/default python
- **THEN** sync includes it without questions or substituting a temporal language override

#### Scenario: Condition changes between syncs
- **WHEN** a previously published attachment's condition becomes false and sync is run again
- **THEN** its managed output is removed while other guidance remains

#### Scenario: Environment changes without sync
- **WHEN** an observed fact changes after publication
- **THEN** the compiled configuration remains unchanged until another sync

#### Scenario: Invalid result
- **WHEN** an eligible condition returns a non-Boolean or raises
- **THEN** sync diagnoses it and publishes no partial managed output

### Requirement: Reconciliation preserves ownership and per-attachment provenance

Each generated attachment SHALL carry a distinct deterministic caret identifier derived from its qualified context reference, destination, and attachment identity. Several attachments from one context SHALL NOT share a single resource-only identifier. A declared attachment id SHALL provide its identity when present; otherwise its one-based ordinal within that destination SHALL apply. These static contributions SHALL NOT use the reserved ^pspec dispatcher identifier.

Sync SHALL replace, insert, or remove only its recognizably managed contributions, preserving user-owned guidance, schema selection, unrelated fields, and comments. Scalar context guidance SHALL use an explicitly delimited managed region; rules and operation guidance SHALL retain separate managed list entries. Ambiguous/malformed ownership markers or incompatible destination types SHALL fail rather than risk consuming user content. Removing a selected context or attachment SHALL remove its obsolete managed output. Identical inputs and observations SHALL produce deterministic content and an identical second sync SHALL leave bytes unchanged. No separate tracking file SHALL be required.

#### Scenario: One context supplies multiple entries
- **WHEN** the Python CLI context supplies several context attachments
- **THEN** each generated contribution has its own identifier and can be distinguished from the others

#### Scenario: Handwritten guidance survives
- **WHEN** config.yaml contains user guidance outside managed regions and entries plus unrelated configuration and comments
- **THEN** reconciliation preserves them while updating managed contributions

#### Scenario: Profile contribution is removed
- **WHEN** a context previously published by sync is no longer selected
- **THEN** its managed output is removed without removing unrelated or handwritten guidance

#### Scenario: Repeat sync
- **WHEN** the same inputs and observations are synchronized twice
- **THEN** the second invocation reports no change and leaves target bytes unchanged

### Requirement: Publication completes before success is reported

Compilation and reconciliation SHALL complete before replacement of the target config.yaml. Errors in inputs, conditions, references, YAML, markers, or publication SHALL return nonzero diagnostics and SHALL NOT claim synchronization success. Pre-publication failures SHALL leave the original target unchanged. Powerspec publication SHALL modify only its owning config.yaml, leaving profiles, resource sources, consumer TOML, temporal values, and installations unchanged. This publication guarantee SHALL NOT imply isolation or rollback of trusted condition/probe effects. Successful output SHALL identify the target and distinguish updated from unchanged configuration.

#### Scenario: Late compilation failure
- **WHEN** one selected attachment fails after earlier attachments have compiled
- **THEN** sync reports failure and leaves the existing configuration bytes unchanged

#### Scenario: Successful publication
- **WHEN** the complete generated document is valid and publication succeeds
- **THEN** sync reports the owning target as updated and leaves other project and agent files unchanged

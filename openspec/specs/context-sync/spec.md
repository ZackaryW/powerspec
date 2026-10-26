# Context Sync Specification

## Purpose

Publish compile-time context guidance into its owning OpenSpec configuration while preserving user content and keeping runtime traits and skill procedures independently resolved.

## Requirements

### Requirement: Sync selects only compile-time contexts

Both pspec sync and powerspec sync SHALL use the nearest owning consumer within the enclosing Git boundary, including nested consumers and worktrees, and select contexts contributed by its effective profiles, with exclusions and subprofile composition following profile-skill-bundles. Runtime traits SHALL NOT be compiled, dispatched or converted into commands in config.yaml. A missing consumer or missing or malformed target configuration SHALL produce diagnostics, not guessed initialization.

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

Context compilation SHALL use persistent config.toml shared variables, selected-profile defaults, global-profile defaults, then context declaration defaults, never current.toml, change-specific values or prompts. Invalid explicit or missing required values SHALL produce diagnostics without fallback. Explicit `<skill:name>` references SHALL render as declared names from the validated catalog without native installation or embedded procedures.

#### Scenario: Reviewed tooling defaults
- **WHEN** the Python CLI context compiles with the profile defaults and an explicit utility_path
- **THEN** its guidance identifies uv, pytest, uv run pytest, and the configured utility location without a prompt or tool installation

#### Scenario: Temporal override does not compile
- **WHEN** current.toml or a change table supplies another test_command
- **THEN** sync still uses shared persistent/default values and leaves those runtime files unchanged

#### Scenario: Skill reference is available as a resource
- **WHEN** an attachment references pspec-tdd from a validated catalog
- **THEN** its published guidance names that skill and identifies its dynamic-resolution requirement from the manifest without executing or embedding its procedure

#### Scenario: Broken temporal file does not affect compilation
- **WHEN** shared persistent context inputs are valid but current.toml contains malformed runtime state
- **THEN** sync compiles without reading that temporal file, preserving it for separate runtime diagnosis

#### Scenario: Input-only manifest
- **WHEN** a mentioned skill has a valid manifest with inputs and no dynamic additions
- **THEN** it is classified as requiring dynamic resolution without requesting those inputs during sync

#### Scenario: All dynamic branches are currently inactive
- **WHEN** a mentioned skill has a valid manifest whose additions would be inactive under current runtime values
- **THEN** it remains classified as requiring dynamic resolution without consulting those runtime values

#### Scenario: Ordinary skill
- **WHEN** a referenced catalog skill has no pspec.toml
- **THEN** its ordinary name is rendered without a requirement to call Powerspec or obtain a null result

#### Scenario: Malformed referenced manifest
- **WHEN** a referenced resource has an unreadable or invalid pspec.toml
- **THEN** sync identifies the resource and fails before publishing any change to config.yaml

#### Scenario: Literal text is not a new reference
- **WHEN** variable substitution introduces text resembling `<skill:name>` or prose contains a bare skill name
- **THEN** that text is not recursively classified or used to add a dynamic-resolution heading

#### Scenario: Unknown skill reference
- **WHEN** an attachment references a skill name that the selected catalog does not declare
- **THEN** compilation fails instead of silently omitting the reference

#### Scenario: Placeholders are substituted once
- **WHEN** guidance contains declared variable placeholders and other angle-bracket prose
- **THEN** each declared placeholder is substituted exactly once and the other prose stays literal

### Requirement: Context conditions produce a compilation snapshot

Sync SHALL evaluate eligible attachment Python when expressions through the shared condition contract with invocation cwd, environment, Git root and persistent context vars, excluding temporal and change values. Omission SHALL be unconditional and false SHALL omit only that attachment. Syntax, name, non-Boolean, capability and probe errors SHALL fail compilation without partial output, and results SHALL NOT be persisted as answers. Published guidance SHALL remain a snapshot until another sync.

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

#### Scenario: Service readiness stays with traits
- **WHEN** guidance depends on mutable runtime service readiness
- **THEN** that readiness remains trait-owned and config.yaml is not implicitly re-evaluated

#### Scenario: Conditions are trusted, not sandboxed
- **WHEN** a condition has side effects or runs for a long time
- **THEN** sync keeps the trusted-rule contract without promising sandboxing, complete execution-time limits, or rollback of callback effects

### Requirement: Reconciliation preserves ownership and per-attachment provenance

Each generated attachment SHALL carry a distinct deterministic caret identifier from its qualified context reference, destination and attachment identity, which is the declared attachment id or else its one-based ordinal in that destination. Attachments from one context SHALL NOT share an identifier or use the reserved ^pspec identifier. Sync SHALL replace, insert or remove only recognizably managed contributions, preserving user guidance, schema selection, unrelated fields and comments.

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

#### Scenario: Attachment without a declared id
- **WHEN** an attachment declares no id
- **THEN** its identity is its one-based ordinal within its destination

### Requirement: Publication completes before success is reported

Compilation and reconciliation SHALL complete before the target config.yaml is replaced. Errors in inputs, conditions, references, YAML, markers or publication SHALL return nonzero diagnostics without claiming success, and pre-publication failures SHALL leave the target unchanged. Publication SHALL modify only the owning config.yaml. This guarantee SHALL NOT imply rollback of trusted condition or probe effects. Successful output SHALL identify the target and whether it was updated or unchanged.

#### Scenario: Late compilation failure
- **WHEN** one selected attachment fails after earlier attachments have compiled
- **THEN** sync reports failure and leaves the existing configuration bytes unchanged

#### Scenario: Successful publication
- **WHEN** the complete generated document is valid and publication succeeds
- **THEN** sync reports the owning target as updated and leaves other project and agent files unchanged

### Requirement: Dynamic-resolution reminders accompany their owning guidance blocks

Each emitted context attachment mentioning manifest-backed skills SHALL begin with a Markdown heading naming those skills as requiring dynamic resolution, deduplicated in first-mention order, inside that attachment's generated text without new YAML keys or a global skill inventory. Ordinary skills SHALL NOT be listed as dynamic, attachments with only ordinary or no skill references SHALL get no heading, and each attachment SHALL keep its own reminder.

#### Scenario: Mixed and repeated mentions
- **WHEN** an emitted attachment mentions dynamic skill A, ordinary skill B, A again, and dynamic skill C
- **THEN** its section heading lists A and C once in that order, followed by native-selection and dynamic-resolution instructions and the authored body
- **AND** B retains an ordinary mention without a Powerspec prerequisite

#### Scenario: All supported destinations
- **WHEN** eligible attachments with dynamic skill references target context, rules.design, and operations.apply.guidance
- **THEN** each generated text block contains its own heading without changing the target YAML schema or attachment identifier

#### Scenario: Ineligible attachment
- **WHEN** an attachment's condition evaluates false
- **THEN** neither its body nor its dynamic-resolution heading is emitted

#### Scenario: Dynamic mention removed
- **WHEN** a later sync removes the final dynamic mention or the referenced resource no longer has a manifest
- **THEN** the former heading and reminder disappear while the current body and user-authored content are preserved

#### Scenario: Repeat publication
- **WHEN** the same guidance, references, and manifests are synchronized twice
- **THEN** the second sync reports unchanged and does not duplicate headings or reminders

#### Scenario: Skill is selected but unmentioned
- **WHEN** the bundle selects a dynamic skill but no emitted attachment explicitly references it
- **THEN** sync does not add a heading or a separate invocation instruction for that skill

### Requirement: Sync preserves sources and installations

Sync SHALL reuse existing source materializations without refresh, and SHALL acquire selected sources lacking a materialization, initializing the store and application when needed. It SHALL NOT refresh existing revisions, install or remove skills, register hooks, execute procedures or flush state. Acquisition failures and unusable materializations SHALL produce diagnostics without deleting or replacing data or installed skills, while obsolete managed context guidance is still reconciled.

#### Scenario: Existing materialization is reused
- **WHEN** a selected source already has a materialization
- **THEN** sync uses it without refreshing its revision

#### Scenario: Missing source is acquired
- **WHEN** a selected source has no current materialization
- **THEN** sync acquires it, initializing the store and application if needed

#### Scenario: Failed acquisition preserves data
- **WHEN** acquisition fails or an existing materialization is unusable
- **THEN** sync reports diagnostics without deleting or replacing existing data or installed skills

#### Scenario: Sync has no installation side effects
- **WHEN** sync completes
- **THEN** no skills were installed or removed, no hooks registered, no procedures executed and no state flushed

### Requirement: Compilation classifies mentioned skills by manifest

For each emitted attachment, compilation SHALL classify explicit skill references from the referenced catalog resources: a valid pspec.toml, even with only inputs or inactive additions, means dynamic resolution, and no manifest means ordinary. An unreadable or malformed manifest, or conflicting classification among same-name selected resources, SHALL be a located compilation error. Classification SHALL NOT resolve runtime values, select branches, read branch content, prompt or execute a skill.

#### Scenario: Conflicting classification
- **WHEN** selected resources sharing a referenced name disagree on whether a manifest exists
- **THEN** compilation reports a located error instead of choosing one

#### Scenario: Unmentioned skill is not classified
- **WHEN** a selected skill is not explicitly referenced by any emitted attachment
- **THEN** it gets no heading and its manifest is not validated for classification

### Requirement: Managed regions are explicit and deterministic

Scalar context guidance SHALL use an explicitly delimited managed region, while rules and operation guidance keep separate managed list entries. Ambiguous or malformed ownership markers or incompatible destination types SHALL fail rather than consume user content. Removing a selected context or attachment SHALL remove its managed output. Identical inputs and observations SHALL produce identical bytes, without a separate tracking file.

#### Scenario: Ambiguous ownership marker
- **WHEN** config.yaml contains a malformed or ambiguous managed marker
- **THEN** sync fails without rewriting the surrounding content

#### Scenario: Incompatible destination type
- **WHEN** a destination exists with a type that cannot hold managed output
- **THEN** sync fails rather than replacing that value

#### Scenario: No tracking file
- **WHEN** sync reconciles managed output
- **THEN** it relies on the markers in config.yaml and needs no separate tracking file

### Requirement: Dynamic reminders direct native selection

Reminder instructions SHALL direct the agent to select the skill through its native integration and supply that location to Powerspec before following its dynamic procedure, only when the skill is invoked under the attachment's task conditions; publication SHALL NOT activate a workflow. Generated configuration SHALL NOT embed authoring-source paths as native-selected locations, and the authored body and per-attachment provenance SHALL stay intact.

#### Scenario: Publication activates nothing
- **WHEN** sync publishes a dynamic-resolution reminder
- **THEN** no workflow or skill is started by that publication

#### Scenario: No authoring paths as selected locations
- **WHEN** a reminder is generated for a catalog skill
- **THEN** it does not present the skill's authoring-source path as the native-selected location

### Requirement: Dynamic reminders are managed with their attachment

The reminder SHALL be managed as part of its owning contribution, so a later sync removes or updates it when mentions, classification or attachment eligibility change. Repeated sync with identical inputs SHALL stay byte-idempotent and preserve handwritten guidance and unrelated YAML.

#### Scenario: Newly dynamic skill gains a reminder
- **WHEN** a mentioned resource gains a valid manifest before the next sync
- **THEN** that sync adds the skill to its attachment's reminder heading

#### Scenario: Handwritten guidance beside a reminder survives
- **WHEN** user guidance sits next to a managed reminder
- **THEN** updating or removing the reminder leaves that guidance unchanged

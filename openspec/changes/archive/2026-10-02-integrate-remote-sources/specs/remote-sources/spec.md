## Purpose

Declare remote recipes in profiles, materialize them through one Powerspec Saucepan application, and connect their validated resources and provenance to existing selection and provisioning.

## ADDED Requirements

### Requirement: Remote acquisition uses profile recipes and one Saucepan application

Profiles SHALL declare each friendly Git source alias with an exact provider, origin, and reference recipe. Powerspec SHALL merge declarations across the effective profile graph, accept identical declarations, reject conflicting recipes for one alias, and reserve `builtin`. Every selected recipe SHALL be materialized through one Saucepan application named `powerspec`; friendly aliases SHALL NOT become Saucepan applications.

Init SHALL lazily initialize the Saucepan store and register the Powerspec application when a selected recipe needs materialization. It SHALL acquire a missing selected recipe and reuse an existing exact materialization without refresh. Sync and ordinary installed skill lookup SHALL NOT initialize, register, acquire, update, or install sources. Upgrade SHALL explicitly reacquire selected recipes. Acquisition failures SHALL identify the affected alias and SHALL NOT report success.

#### Scenario: Fresh init needs a remote recipe
- **WHEN** init selects a declared recipe and no Powerspec Saucepan store or application exists
- **THEN** Powerspec initializes one store, registers the `powerspec` application, acquires the recipe, and retains its provenance

#### Scenario: Repeated init finds a materialization
- **WHEN** init selects a recipe already materialized in the Powerspec application
- **THEN** it reuses the current materialization without refreshing it

#### Scenario: Conflicting aliases
- **WHEN** two effective profiles declare different recipes for the same source alias
- **THEN** composition fails before Saucepan or installation work begins

#### Scenario: Read an installed remote skill
- **WHEN** `pspec skill` resolves an already installed skill originally obtained remotely
- **THEN** no Saucepan fetch, source update, or installation occurs

### Requirement: Only valid source catalogs become registered bindings

Powerspec SHALL discover .pspec resources for reusable catalog registration and bind validated catalogs to an explicit external identity. A requested reusable catalog containing no .pspec SHALL NOT remain bound. Direct @gitsource skill-path references SHALL follow their separate selection contract without requiring a remote .pspec catalog. Invalid or ambiguous catalogs SHALL produce source-specific diagnostics rather than a partial successful registration or source-order selection. Registration SHALL preserve existing valid bindings on a failed replacement. The reserved builtin identity SHALL remain unavailable to external registration; folder names SHALL NOT confer builtin identity.

#### Scenario: No catalog in repository
- **WHEN** a repository acquired for reusable catalog registration contains no .pspec resource catalog
- **THEN** Powerspec cancels the attempted binding and reports the absent catalog without deleting unrelated sources

#### Scenario: Reserved source name
- **WHEN** a remote registration requests builtin
- **THEN** it is rejected without changing the packaged catalog

#### Scenario: Multiple catalogs expose ambiguous names
- **WHEN** discovered catalogs under one source expose duplicate declared skill identities
- **THEN** discovery reports the ambiguity instead of choosing the first path

### Requirement: Remote selection preserves installed names and provenance

A qualified remote skill reference SHALL resolve through its registered source catalog using the name declared in SKILL.md. The selected resource SHALL pass through the existing composition and ZuAT provisioning contracts with its source, revision, and location provenance. Its installed name SHALL remain the declared name without a source prefix. Same-name resources in unselected sources SHALL not conflict; different selected resources targeting the same agent/name/scope/project destination SHALL be diagnosed under the existing selection contract. Remote registration SHALL not itself install a skill.

#### Scenario: Remote skill selected
- **WHEN** a profile selects @team-tools/pspec-tdd from a validated saucepan-managed source
- **THEN** selection retains provenance and provisioning receives the complete resource with installed name pspec-tdd

#### Scenario: Source merely registered
- **WHEN** a newly registered source contains a same-name skill but is not selected
- **THEN** registration performs no install and creates no installation-name conflict

#### Scenario: Selected resource collision
- **WHEN** two different selected source resources share an installed name and target
- **THEN** the existing selection diagnostic identifies both sources before one can overwrite the other

### Requirement: Git source references select declared recipe paths directly

Profile skills SHALL support `@gitsource/<alias>/<path-pattern>` strings. The alias SHALL resolve to a `[[source]]` declaration in the effective profile graph. Powerspec SHALL NOT derive a URL from the alias, create a `sources/` resource folder, or silently bind an undeclared alias. Parsing and runtime arming SHALL retain the alias and selector without fetching. Materialization SHALL use the declared recipe and retain resolved revision and artifact provenance.

Selectors SHALL be source-relative and contained after canonicalization including symlinks. Direct directories SHALL select one skill root; `*` SHALL match immediate child directories and recursive selection SHALL require `**`. Candidate roots SHALL carry `SKILL.md`; unrelated files and folders SHALL not be installed. Empty initial selections, malformed declarations, duplicate declared names, and escaping paths SHALL produce diagnostics. A valid upgrade replacement may be empty for an established selection. Expansion SHALL be deterministic by source-relative path.

Direct Git-path selection SHALL NOT require `.pspec` or write synthetic catalog files into the acquired checkout. Each selected skill SHALL retain its complete resources, declared installed name, alias, source/revision/path provenance, and declaring profile scope.

#### Scenario: Zmem wildcard selects its skills
- **WHEN** a profile declares the zmem recipe and selects `@gitsource/zmem/skills/*`
- **THEN** selection uses that recipe's materialization and yields its declared immediate skills with external provenance and unprefixed names

#### Scenario: Alias has no declaration
- **WHEN** a reference names a Git source alias absent from the effective profile declarations
- **THEN** resolution reports the missing declaration without guessing a URL or treating the alias as a Saucepan app

#### Scenario: Direct selection
- **WHEN** a reference selects one contained source-relative directory with a valid `SKILL.md`
- **THEN** only that complete skill root participates

#### Scenario: Selector escapes or has no skill matches
- **WHEN** a selector is absolute, escapes after canonicalization, or an initial selection has no skill roots
- **THEN** selection reports the relevant diagnostic without installing unrelated files

#### Scenario: Runtime doctor condition is false
- **WHEN** the lifecycle profile selects external skills but its runtime trait condition is false
- **THEN** skill selection and checkpoint context remain selected while only that trait guidance is omitted

### Requirement: Sync reuses materialized sources and preserves installations

Sync SHALL resolve declared recipes only from existing materializations in the `powerspec` Saucepan application without refreshing or fetching sources. Sync SHALL NOT install or remove skills, including when a source is unavailable or its registration has been removed. Required resources missing from existing materialization SHALL produce diagnostics without attempting repair. These installation guarantees SHALL NOT prevent normal config.yaml reconciliation of obsolete managed context contributions.

#### Scenario: Sync while source is unavailable
- **WHEN** a selected recipe has no readable current materialization during sync
- **THEN** sync performs no refresh or installed-skill removal and reports any missing required resource without silently acquiring it

### Requirement: Upgrade removes obsolete skills only on complete success

An explicit upgrade SHALL refresh selected profile recipes through the `powerspec` Saucepan application, validate replacement selections, and provision selected complete resources through ZuAT. Missing skills SHALL be confirmed only by a successfully refreshed, valid recipe. Failed acquisition, an unavailable application, an unmatched recipe, and invalid replacements SHALL NOT establish absence.

Removal SHALL be limited to obsolete managed copies in requested installation targets, preserving copies still required by another effective selection and unrelated installations. Every requested source refresh, selection validation, collision check, and provisioning step SHALL succeed before removal is committed. Any failure of the requested upgrade, including removal finalization, SHALL preserve prior installed copies from obsolete-skill removal and SHALL NOT report upgrade success. Unsupported recoverable removal capabilities SHALL produce a diagnostic without deletion. This requirement SHALL NOT imply rollback of source caches or all non-removal updates.

#### Scenario: Successful upgrade removes a disappeared skill
- **WHEN** a valid refreshed source no longer contains a previously selected managed skill and the entire requested upgrade succeeds
- **THEN** upgrade commits removal of its obsolete managed copy while preserving unrelated and still-selected copies

#### Scenario: Last wildcard match disappears
- **WHEN** a valid refreshed source yields an empty replacement for an established wildcard selection and the entire requested upgrade succeeds
- **THEN** upgrade may remove its obsolete managed copies without treating the confirmed empty replacement as a failed initial selection

#### Scenario: Explicit source registration removal
- **WHEN** evidence establishes explicit removal of a previously bound source registration and the entire requested upgrade succeeds
- **THEN** upgrade may remove its obsolete managed copies without inferring deletion from an unknown-source diagnostic alone

#### Scenario: Another source fails later
- **WHEN** one source confirms a disappeared skill but another requested refresh or provisioning step fails
- **THEN** the upgrade reports failure and preserves the obsolete installed copy without committing removals

#### Scenario: Removal finalization fails
- **WHEN** removal finalization cannot complete for the whole requested upgrade
- **THEN** no partially committed removals remain and upgrade reports failure rather than success

#### Scenario: Recursive selector is explicit
- **WHEN** a registered source contains valid skills at immediate and nested depths
- **THEN** skills/* selects only immediate skill roots and an explicitly recursive ** selector can select nested roots within the same canonical source boundary

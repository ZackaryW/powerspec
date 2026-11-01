# Spec Delta

## MODIFIED Requirements

### Requirement: Remote acquisition uses profile recipes and one Saucepan application

Profiles SHALL declare each friendly Git source alias with an exact provider, origin and reference recipe, merged across the profile graph: identical declarations are accepted, conflicting ones rejected, and builtin reserved. Every selected recipe SHALL be materialized through Powerspec's managed milkpan as a lease on its resolved commit in the owning consumer's scope; aliases SHALL NOT become scopes. Consumers SHALL update independently while sharing stored content for the same commit.

#### Scenario: Fresh init needs a remote recipe
- **WHEN** init selects a declared recipe and no milkpan home or selection exists
- **THEN** Powerspec prepares milkpan, resolves the recipe's reference, leases that exact commit in the consumer's scope and retains the selection with provenance

#### Scenario: Repeated init finds a materialization
- **WHEN** ordinary init without --force selects a recipe already materialized for this consumer
- **THEN** it reuses that selected binding without refreshing it

#### Scenario: Conflicting aliases
- **WHEN** two effective profiles declare different recipes for one alias
- **THEN** composition fails before milkpan or installation work begins

#### Scenario: Read an installed remote skill
- **WHEN** ordinary skill resolution reads an already installed skill originally obtained remotely
- **THEN** no source fetch, update, installation or retention mutation occurs

#### Scenario: Two consumers share one origin
- **WHEN** one consumer upgrades a source also selected by another consumer
- **THEN** only the upgrading consumer's selected binding changes while the other consumer retains its chosen output

### Requirement: Remote selection preserves installed names and provenance

A qualified remote skill reference SHALL resolve through its registered source catalog by the name declared in SKILL.md, and pass through composition and ZuAT provisioning with its source, revision and location provenance, installed under that declared name without a source prefix. Same-name resources in unselected sources SHALL NOT conflict, while different selected resources targeting one agent/name/scope/project destination SHALL be diagnosed. Registration alone SHALL NOT install a skill.

#### Scenario: Remote skill selected
- **WHEN** a profile selects @team-tools/pspec-tdd from a validated milkpan-managed source
- **THEN** selection retains provenance and provisioning receives the complete resource with installed name pspec-tdd

#### Scenario: Source merely registered
- **WHEN** a newly registered source contains a same-name skill but is not selected
- **THEN** registration performs no install and creates no installation-name conflict

#### Scenario: Selected resource collision
- **WHEN** two different selected source resources share an installed name and target
- **THEN** the existing selection diagnostic identifies both sources before one can overwrite the other

### Requirement: Git source references select declared recipe paths directly

Profile skills SHALL support `<alias>/<path-pattern>` strings for Git-path selection, where the alias names a `[[source]]` declaration in the effective profile graph and the rest is the selector. Powerspec SHALL NOT derive URLs from aliases, create a `sources/` folder, bind undeclared aliases or require an `@gitsource` namespace. Parsing, status and arming SHALL keep alias and selector without fetching, and materialization SHALL use the declared recipe with revision and artifact provenance.

#### Scenario: Zmem wildcard selects its skills
- **WHEN** a profile declares the zmem recipe and selects `zmem/skills/*`
- **THEN** selection uses that recipe's materialization and yields its declared immediate skills with external provenance and unprefixed names

#### Scenario: Alias has no declaration
- **WHEN** a source-relative reference names an alias absent from the effective profile declarations
- **THEN** resolution reports the missing declaration without guessing a URL or treating the alias as a milkpan scope

#### Scenario: Direct selection
- **WHEN** a reference selects one contained source-relative directory with a valid `SKILL.md`
- **THEN** only that complete skill root participates

#### Scenario: Selector escapes or has no skill matches
- **WHEN** a selector is absolute, escapes after canonicalization, or an initial selection has no skill roots
- **THEN** selection reports the relevant diagnostic without installing unrelated files

#### Scenario: Runtime doctor condition is false
- **WHEN** the lifecycle profile selects external skills but its runtime trait condition is false
- **THEN** skill selection and checkpoint context remain selected while only that trait guidance is omitted

#### Scenario: Legacy namespace is rejected
- **WHEN** a profile supplies an `@gitsource/<alias>/<path-pattern>` skill string
- **THEN** validation reports the unsupported legacy syntax and directs migration to `<alias>/<path-pattern>`

### Requirement: Sync reuses materialized sources and preserves installations

Sync SHALL resolve declared recipes only from the consumer's existing milkpan selections, without refreshing or fetching. It SHALL NOT install or remove skills, even when a source is unavailable or its selection was removed. Required resources missing from an existing materialization SHALL produce diagnostics without repair. These guarantees SHALL NOT prevent normal config.yaml reconciliation of obsolete managed context contributions.

#### Scenario: Sync while source is unavailable
- **WHEN** a selected recipe has no readable current materialization during sync
- **THEN** sync performs no refresh or installed-skill removal and reports any missing required resource without silently acquiring it

### Requirement: Upgrade removes obsolete skills only on complete success

An explicit upgrade SHALL refresh selected profile recipes through milkpan (resolving each reference again), validate replacement selections, and provision selected complete resources through ZuAT. Missing skills SHALL be confirmed only by a successfully refreshed, valid recipe; failed acquisition, unavailable milkpan, an unmatched recipe and invalid replacements SHALL NOT establish absence.

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

## REMOVED Requirements

### Requirement: Profile defaults are expanded by the manager
**Reason**: Milkpan has no profile expansion or policy catalogs; freshness comes from lease settings in Powerspec's policy file.
**Migration**: See "Source freshness uses lease settings".

## ADDED Requirements

### Requirement: Source freshness uses lease settings
Preparing a missing selection SHALL resolve the recipe's reference at most once per day per consumer, reusing a resolution within that day without network access. Upgrade and init --force SHALL resolve again regardless of age. Selected commit leases SHALL NOT expire while selected. A selection SHALL be published only after the caller's success boundary, and a replaced selection's lease SHALL be released only after the new one is published.

#### Scenario: Second consumer within a day
- **WHEN** another consumer prepares a recipe whose commit is already stored
- **THEN** no content is downloaded and that consumer gets its own commit lease

#### Scenario: Upgrade fails after resolving
- **WHEN** upgrade resolves a new commit but a later step fails
- **THEN** the consumer keeps its previous selection and content, and the candidate lease is released

### Requirement: Only GitHub and local origins are supported
Recipes with `https://github.com/<owner>/<repo>` origins (optionally ending in `.git`) SHALL map to milkpan GitHub specs, and recipes with absolute local paths or `file://` URLs SHALL map to milkpan local specs. Any other origin SHALL fail with a configuration error naming the supported forms, before milkpan is invoked.

#### Scenario: GitLab origin
- **WHEN** a recipe's origin is `https://gitlab.com/team/tools`
- **THEN** preparation fails naming the supported GitHub and local forms

#### Scenario: Local test repository
- **WHEN** a recipe's origin is a `file://` URL of a local repository
- **THEN** it is prepared through milkpan's local provider at the recipe's reference

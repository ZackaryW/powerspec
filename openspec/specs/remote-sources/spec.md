# Remote Sources Specification

## Purpose

Declare remote recipes in profiles, materialize them through one Powerspec Saucepan application, and connect their validated resources and provenance to existing selection and provisioning.

## Requirements

### Requirement: Remote acquisition uses profile recipes and one Saucepan application

Profiles SHALL declare each friendly Git source alias with an exact provider, origin and reference recipe, merged across the profile graph: identical declarations are accepted, conflicting ones rejected, and builtin reserved. Every selected recipe SHALL be materialized through one registered Saucepan application named powerspec, identified by its UUID; aliases SHALL NOT become applications. Claims SHALL use owning-consumer scopes, so consumers update independently yet share cached content.

#### Scenario: Fresh init needs a remote recipe
- **WHEN** init selects a declared recipe and no store or application exists
- **THEN** Powerspec initializes the absent store, registers its application and materializes and retains the scoped recipe with provenance

#### Scenario: Repeated init finds a materialization
- **WHEN** ordinary init without --force selects a recipe already materialized for this consumer
- **THEN** it reuses that selected binding without refreshing it

#### Scenario: Conflicting aliases
- **WHEN** two effective profiles declare different recipes for one alias
- **THEN** composition fails before Saucepan or installation work begins

#### Scenario: Read an installed remote skill
- **WHEN** ordinary skill resolution reads an already installed skill originally obtained remotely
- **THEN** no source fetch, update, installation or retention mutation occurs

#### Scenario: Two consumers share one origin
- **WHEN** one consumer upgrades a source also selected by another consumer
- **THEN** only the upgrading consumer's selected binding changes while the other consumer retains its chosen output

### Requirement: Only valid source catalogs become registered bindings

Powerspec SHALL discover .pspec resources for reusable catalog registration and bind validated catalogs to an explicit external identity; a requested catalog with no .pspec SHALL NOT stay bound. Direct @gitsource skill-path references SHALL follow their separate selection contract without a remote .pspec catalog. Invalid or ambiguous catalogs SHALL produce source-specific diagnostics, not partial registration or source-order selection, and a failed replacement SHALL keep existing valid bindings.

#### Scenario: No catalog in repository
- **WHEN** a repository acquired for reusable catalog registration contains no .pspec resource catalog
- **THEN** Powerspec cancels the attempted binding and reports the absent catalog without deleting unrelated sources

#### Scenario: Reserved source name
- **WHEN** a remote registration requests builtin
- **THEN** it is rejected without changing the packaged catalog

#### Scenario: Multiple catalogs expose ambiguous names
- **WHEN** discovered catalogs under one source expose duplicate declared skill identities
- **THEN** discovery reports the ambiguity instead of choosing the first path

#### Scenario: Folder name does not confer builtin identity
- **WHEN** an external catalog lives in a folder named builtin
- **THEN** it does not receive the reserved builtin identity

### Requirement: Remote selection preserves installed names and provenance

A qualified remote skill reference SHALL resolve through its registered source catalog by the name declared in SKILL.md, and pass through composition and ZuAT provisioning with its source, revision and location provenance, installed under that declared name without a source prefix. Same-name resources in unselected sources SHALL NOT conflict, while different selected resources targeting one agent/name/scope/project destination SHALL be diagnosed. Registration alone SHALL NOT install a skill.

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

Profile skills SHALL support `<alias>/<path-pattern>` strings for Git-path selection, where the alias names a `[[source]]` declaration in the effective profile graph and the rest is the selector. Powerspec SHALL NOT derive URLs from aliases, create a `sources/` folder, bind undeclared aliases or require an `@gitsource` namespace. Parsing, status and arming SHALL keep alias and selector without fetching, and materialization SHALL use the declared recipe with revision and artifact provenance.

#### Scenario: Zmem wildcard selects its skills
- **WHEN** a profile declares the zmem recipe and selects `zmem/skills/*`
- **THEN** selection uses that recipe's materialization and yields its declared immediate skills with external provenance and unprefixed names

#### Scenario: Alias has no declaration
- **WHEN** a source-relative reference names an alias absent from the effective profile declarations
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

#### Scenario: Legacy namespace is rejected
- **WHEN** a profile supplies an `@gitsource/<alias>/<path-pattern>` skill string
- **THEN** validation reports the unsupported legacy syntax and directs migration to `<alias>/<path-pattern>`

### Requirement: Sync reuses materialized sources and preserves installations

Sync SHALL resolve declared recipes only from existing materializations in the `powerspec` Saucepan application, without refreshing or fetching. It SHALL NOT install or remove skills, even when a source is unavailable or its registration was removed. Required resources missing from an existing materialization SHALL produce diagnostics without repair. These guarantees SHALL NOT prevent normal config.yaml reconciliation of obsolete managed context contributions.

#### Scenario: Sync while source is unavailable
- **WHEN** a selected recipe has no readable current materialization during sync
- **THEN** sync performs no refresh or installed-skill removal and reports any missing required resource without silently acquiring it

### Requirement: Upgrade removes obsolete skills only on complete success

An explicit upgrade SHALL refresh selected profile recipes through the `powerspec` Saucepan application, validate replacement selections, and provision selected complete resources through ZuAT. Missing skills SHALL be confirmed only by a successfully refreshed, valid recipe; failed acquisition, an unavailable application, an unmatched recipe and invalid replacements SHALL NOT establish absence.

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

### Requirement: Profile defaults are expanded by the manager

Authorized preparation SHALL obtain Saucepan's `explicit-update` expansion and register its immutable flat catalog. Missing-selection preparation SHALL override retrieval refresh with max_age 86400 seconds; upgrade and init --force SHALL use always-refresh and acquisition-update; pin retention, consumer scope and optional protection SHALL stay independent. Pending intent SHALL keep the expanded catalog and UUIDs for retry, and read-only lookup SHALL NOT expand or register profiles.

#### Scenario: Preparation response is lost after selecting policies
- **WHEN** an uncertain preparation is retried
- **THEN** the original expanded catalog and UUID references are reused without expanding the named recipe again

#### Scenario: Explicit upgrade updates copied results
- **WHEN** an existing selected recipe is explicitly upgraded
- **THEN** the manager-expanded profile uses the explicitly supplied acquisition-update policy before revision-checked claim adoption and preparation

#### Scenario: Initialization selects bounded freshness
- **WHEN** ordinary init prepares a missing consumer selection
- **THEN** its expanded policies use cached retrieval with a 86400-second maximum age and retain manual copied-result updates and consumer-scoped pins

#### Scenario: Forced initialization selects explicit refresh
- **WHEN** init --force prepares a selected recipe
- **THEN** the expanded policies force retrieval and copied-result updates even when the existing consumer selection and shared cache are current

### Requirement: Selected bindings retain exact output provenance

Each selected remote binding SHALL retain its source identity, selector, resolved revision, output identity, contained relative view and explicit retention receipt, and validation and provisioning SHALL use manager-returned paths backed by that retention. Source refresh SHALL produce candidate bindings that are not published as selections until validation succeeds. Prior selected outputs SHALL stay available to existing readers; no automatic retention release SHALL race read-only lookups.

#### Scenario: Origin advances before sync
- **WHEN** the origin has a newer commit but only sync or status is requested
- **THEN** Powerspec reports and uses the previously selected retained revision without fetching

#### Scenario: Invalid replacement
- **WHEN** a refreshed repository fails catalog or skill selection validation
- **THEN** Powerspec preserves its prior selected binding, retention and installed copies and reports failure

#### Scenario: First selection survives provisioning failure
- **WHEN** init --agent prepares and validates a source that the consumer has never selected, and a selected skill then fails provisioning
- **THEN** the validated binding is published as the consumer's selection
- **AND** a following `pspec upgrade --agent <agent>` or `pspec sync` finds that selection instead of reporting that no materialization is selected

#### Scenario: Replacement withheld on provisioning failure
- **WHEN** init --agent --force validates a replacement for an existing selection and agent provisioning then fails
- **THEN** the prior selection remains published and the replacement is not published

#### Scenario: Full-repository lookup
- **WHEN** profile selection needs a resource beneath an acquired repository
- **THEN** the path is contained within the manager-returned selected view and not reconstructed from store layout

#### Scenario: Concurrent reclamation
- **WHEN** manager cache reclamation runs during a read-only lookup of a selected binding
- **THEN** the explicitly retained output remains readable without requiring the lookup to mutate retention

### Requirement: Source integration preserves structured failures
Powerspec SHALL distinguish unavailable metadata, denied authority, inconsistent state, revision conflicts and potentially committed mutations through current structured manager/transport results. Diagnostic text matching SHALL NOT decide whether to initialize or reset a store. Protected failures SHALL NOT trigger unrestricted retries. A lost response SHALL be reconciled using the original operation identity before new mutations or cleanup.

#### Scenario: Missing registration during lookup
- **WHEN** read-only lookup cannot find this consumer's application or binding
- **THEN** it reports unavailable metadata without registering or repairing anything

#### Scenario: Denied protected context
- **WHEN** the manager denies the configured app context
- **THEN** Powerspec preserves the denial and performs no unbound retry or credential reset

#### Scenario: Lost preparation receipt
- **WHEN** preparation may have committed but no valid response arrived
- **THEN** Powerspec reconciles its saved key and expected revision and does not create a replacement identity blindly

### Requirement: New consumers reuse recent shared source material
Ordinary init SHALL reuse valid manager-cached retrieval material younger than 86400 seconds for a missing consumer selection. Missing, expired, or future-dated freshness evidence SHALL require retrieval under provider policy. Existing consumer selections SHALL remain pinned without refresh regardless of age. Cache age SHALL be measured by the manager from retrieval evidence, not reset by consumer initialization. A required refresh failure SHALL fail initialization without stale fallback.

#### Scenario: A second folder shares a warm cache
- **WHEN** a new consumer selects the same source and reference less than 24 hours after successful retrieval
- **THEN** init creates its own retained selection without cloning or fetching that source and preserves the first consumer's selection

#### Scenario: Cache expires
- **WHEN** a new consumer selects cached material whose successful retrieval is at least 86400 seconds old
- **THEN** init refreshes upstream before committing its selection

#### Scenario: Empty cache
- **WHEN** a new consumer has no usable shared retrieval material
- **THEN** init retrieves the source and retains the validated output

#### Scenario: Existing consumer outlives the freshness window
- **WHEN** ordinary init repeats for an existing valid selection after 24 hours
- **THEN** it reuses the exact pinned revision without a fetch

#### Scenario: Warm cache is usable offline
- **WHEN** a new consumer selects valid shared material younger than 24 hours and upstream is unavailable
- **THEN** init succeeds from cached material without contacting upstream

#### Scenario: Expired cache is offline
- **WHEN** retrieval is required and upstream is unavailable
- **THEN** init fails without committing a replacement selection or silently accepting stale material

#### Scenario: Forced refresh fails
- **WHEN** init --force cannot retrieve or validate a replacement
- **THEN** it fails and preserves prior selected bindings and pins under the existing recovery contract

### Requirement: Only init and upgrade prepare sources

Ordinary init SHALL lazily initialize an absent store and register the application when a selected recipe needs materialization, acquiring missing recipes and reusing exact selected bindings without refresh. Upgrade and init --force SHALL refresh selected recipes, including existing selections. Sync, status, hooks and installed skill lookup SHALL NOT initialize, register, acquire, update, pin, unpin or install sources. Acquisition failures SHALL name the alias without reporting success.

#### Scenario: Forced init refreshes existing selections
- **WHEN** init --force runs for a consumer with existing source selections
- **THEN** those selected recipes are explicitly refreshed

#### Scenario: Acquisition failure names the alias
- **WHEN** acquiring a selected recipe fails
- **THEN** the command identifies that alias and does not report success

#### Scenario: Default registration needs no credentials
- **WHEN** the application is registered with default settings
- **THEN** neither credentials nor native keyring integrity are required, while explicitly configured restrictions stay enforced

### Requirement: Git path selectors are contained and deterministic

Selectors SHALL stay contained after canonicalization, including symlinks. A direct directory SHALL select one skill root, `*` SHALL match immediate child directories, and recursion SHALL require `**`; candidate roots SHALL carry SKILL.md and unrelated files SHALL NOT be installed. Empty initial selections, malformed declarations, duplicate names and escaping paths SHALL be diagnosed; an established selection's upgrade replacement MAY be empty. Expansion SHALL be ordered by source-relative path.

#### Scenario: Symlink escape is rejected
- **WHEN** a selector reaches outside the source through a symbolic link
- **THEN** selection reports the escaping path

#### Scenario: Single star does not recurse
- **WHEN** a selector ends in `*`
- **THEN** only immediate child directories carrying SKILL.md are selected

#### Scenario: Expansion order is stable
- **WHEN** a wildcard matches several skill roots
- **THEN** they are expanded in source-relative path order

#### Scenario: Empty upgrade replacement for an established selection
- **WHEN** an upgrade refreshes an established selection whose selector now matches nothing
- **THEN** the empty replacement is valid rather than an error

### Requirement: Direct Git-path selection keeps complete provenance

Direct Git-path selection SHALL NOT require `.pspec` or write synthetic catalog files into the acquired checkout. Each selected skill SHALL keep its complete resources, declared installed name, alias, source/revision/path provenance and declaring profile scope. Legacy `@gitsource/...` strings SHALL be rejected rather than kept as a second authored syntax.

#### Scenario: No catalog files are written
- **WHEN** a direct Git-path selection is materialized
- **THEN** no synthetic catalog files are written into the acquired checkout

#### Scenario: Selected skill keeps its provenance
- **WHEN** a skill is selected through a Git path
- **THEN** it carries its alias, source, revision, path and declaring profile scope

### Requirement: Obsolete skill removal is limited and committed last

Removal SHALL be limited to obsolete managed copies in requested targets, keeping copies another effective selection needs and unrelated installations. Every requested refresh, validation, collision check and provisioning step SHALL succeed before removal is committed; any failure, including removal finalization, SHALL keep prior copies and SHALL NOT report success. Unsupported recoverable removal SHALL be diagnosed without deletion, and this SHALL NOT imply rollback of caches or other updates.

#### Scenario: Still-required copy is kept
- **WHEN** an obsolete skill in one selection is still required by another effective selection
- **THEN** upgrade keeps that installed copy

#### Scenario: Unsupported recoverable removal
- **WHEN** the agent target cannot remove a skill recoverably
- **THEN** upgrade reports a diagnostic and deletes nothing

### Requirement: Selection publication depends on prior selection

A validated candidate for a recipe with no prior selection in the consumer SHALL be published before agent provisioning, so a later skill or hook provisioning failure, or a declined replacement, does not discard it. A candidate replacing an existing selection SHALL be published only when the entire requested initialization succeeds; otherwise the prior selection SHALL remain.

#### Scenario: Declined replacement keeps the first selection
- **WHEN** the user declines to replace conflicting skills during a consumer's first init
- **THEN** the consumer's validated first source selection stays published

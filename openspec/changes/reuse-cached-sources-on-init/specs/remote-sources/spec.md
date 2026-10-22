# Spec Delta

## MODIFIED Requirements

### Requirement: Remote acquisition uses profile recipes and one Saucepan application
Profiles SHALL declare each friendly Git source alias with an exact provider, origin and reference recipe. Powerspec SHALL merge declarations across the effective profile graph, accept identical declarations, reject conflicting recipes for one alias and reserve builtin. Every selected recipe SHALL be materialized through one registered Saucepan application named powerspec, identified by its returned UUID. Friendly aliases SHALL NOT become Saucepan applications. Claims SHALL use explicit owning-consumer scopes so independent consumers can update separately while sharing cached content.

Ordinary init SHALL lazily initialize an absent store and register the application when a selected recipe needs materialization. It SHALL acquire and retain a missing selected recipe and reuse an existing exact selected binding without refresh. Sync, status, hooks and ordinary installed skill lookup SHALL NOT initialize, register, acquire, update, pin, unpin or install sources. Upgrade and init --force SHALL explicitly refresh selected recipes, including existing consumer selections. Acquisition failures SHALL identify the affected alias and SHALL NOT report success. Default registration SHALL require neither credentials nor native keyring integrity, while explicitly configured restrictions SHALL remain enforced.

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

### Requirement: Profile defaults are expanded by the manager
Authorized preparation SHALL obtain the `explicit-update` expansion from Saucepan and register its immutable flat catalog. Ordinary missing-selection preparation SHALL supply a retrieval-refresh override with max_age of 86400 seconds. Explicit upgrade and init --force SHALL supply always-refresh and acquisition-update overrides; pin retention, consumer scope and optional protection SHALL remain independent. Pending intent SHALL retain the expanded catalog and UUID references for retry; read-only lookup SHALL NOT expand or register profiles.

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


## ADDED Requirements

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

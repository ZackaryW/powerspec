# Remote Sources Delta

## MODIFIED Requirements

### Requirement: Remote acquisition uses profile recipes and one Saucepan application
Profiles SHALL declare each friendly Git source alias with an exact provider, origin and reference recipe. Powerspec SHALL merge declarations across the effective profile graph, accept identical declarations, reject conflicting recipes for one alias and reserve builtin. Every selected recipe SHALL be materialized through one registered Saucepan application named powerspec, identified by its returned UUID. Friendly aliases SHALL NOT become Saucepan applications. Claims SHALL use explicit owning-consumer scopes so independent consumers can update separately while sharing cached content.

Init SHALL lazily initialize an absent store and register the application when a selected recipe needs materialization. It SHALL acquire and retain a missing selected recipe and reuse an existing exact selected binding without refresh. Sync, status, hooks and ordinary installed skill lookup SHALL NOT initialize, register, acquire, update, pin, unpin or install sources. Upgrade SHALL explicitly refresh selected recipes. Acquisition failures SHALL identify the affected alias and SHALL NOT report success. Default registration SHALL require neither credentials nor native keyring integrity, while explicitly configured restrictions SHALL remain enforced.

#### Scenario: Fresh init needs a remote recipe
- **WHEN** init selects a declared recipe and no store or application exists
- **THEN** Powerspec initializes the absent store, registers its application and materializes and retains the scoped recipe with provenance

#### Scenario: Repeated init finds a materialization
- **WHEN** init selects a recipe already materialized for this consumer
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

## ADDED Requirements

### Requirement: Profile defaults are expanded by the manager
Authorized preparation SHALL obtain the `explicit-update` expansion from Saucepan and register its immutable flat catalog. Explicit upgrade SHALL supply an acquisition-update override; pin retention, consumer scope and optional protection SHALL remain independent. Pending intent SHALL retain the expanded catalog and UUID references for retry; read-only lookup SHALL NOT expand or register profiles.

#### Scenario: Preparation response is lost after selecting policies
- **WHEN** an uncertain preparation is retried
- **THEN** the original expanded catalog and UUID references are reused without expanding the named recipe again

#### Scenario: Explicit upgrade updates copied results
- **WHEN** an existing selected recipe is explicitly upgraded
- **THEN** the manager-expanded profile uses the explicitly supplied acquisition-update policy before revision-checked claim adoption and preparation

### Requirement: Selected bindings retain exact output provenance
Each selected remote binding SHALL retain its source identity, selector, resolved revision, output identity, contained relative view and explicit retention receipt. Validation and provisioning SHALL use manager-returned paths backed by that retention. Source refresh SHALL produce candidate bindings without publishing them as Powerspec selections until validation succeeds. Prior selected outputs SHALL remain available for existing readers; no automatic historical retention release SHALL race read-only lookups.

#### Scenario: Origin advances before sync
- **WHEN** the origin has a newer commit but only sync or status is requested
- **THEN** Powerspec reports and uses the previously selected retained revision without fetching

#### Scenario: Invalid replacement
- **WHEN** a refreshed repository fails catalog or skill selection validation
- **THEN** Powerspec preserves its prior selected binding, retention and installed copies and reports failure

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

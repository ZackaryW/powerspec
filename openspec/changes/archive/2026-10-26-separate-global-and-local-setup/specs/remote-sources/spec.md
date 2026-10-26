## MODIFIED Requirements

### Requirement: Selected bindings retain exact output provenance
Each selected remote binding SHALL retain its source identity, selector, resolved revision, output identity, contained relative view and explicit retention receipt. Validation and provisioning SHALL use manager-returned paths backed by that retention. Source refresh SHALL produce candidate bindings without publishing them as Powerspec selections until validation succeeds. A validated candidate for a recipe that has no prior selection in the consumer SHALL be published before agent provisioning, so a later skill or hook provisioning failure, or a declined replacement, does not discard it. A candidate that replaces an existing selection SHALL be published only when the entire requested initialization succeeds; otherwise the prior selection SHALL remain. Prior selected outputs SHALL remain available for existing readers; no automatic historical retention release SHALL race read-only lookups.

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

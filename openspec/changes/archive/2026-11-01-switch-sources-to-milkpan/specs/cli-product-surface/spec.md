# Spec Delta

## MODIFIED Requirements

### Requirement: Synchronization is local-aware and atomic

`pspec sync` SHALL compose bundled, consumer-local and selected remote resources, resolve conditions against the owning consumer, validate every required resource, and only then atomically reconcile managed guidance in `openspec/config.yaml`, preserving user YAML and the original file on failure. It SHALL acquire missing selected sources while reusing existing materializations without refresh, and successful acquisitions SHALL stay available if later validation fails.

#### Scenario: Publish local and bundled contexts
- **WHEN** a consumer-local resource overrides or extends selected bundled guidance and all required resources are available
- **THEN** sync publishes the effective contributions once while preserving user-authored content

#### Scenario: Required source is unavailable
- **WHEN** a selected remote resource is not already materialized
- **THEN** sync attempts its first acquisition; a failure reports the unavailable resource and leaves `config.yaml` byte-for-byte unchanged

#### Scenario: Fresh machine
- **WHEN** selected sources have never been materialized
- **THEN** sync prepares milkpan, acquires those sources, and publishes after complete validation

#### Scenario: Preserve current remote revision
- **WHEN** upstream has newer content than the current materialization
- **THEN** sync reuses the current revision; refreshing it requires upgrade

### Requirement: Upgrade refreshes before committing removals

`pspec upgrade --agent <agent>` SHALL refresh selected milkpan sources, compose the refreshed bundle, reconcile skills and hooks, and remove obsolete managed installations only after every required refresh and reconciliation step succeeds. It SHALL bring Powerspec's managed milkpan to the pinned release before refreshing, effective on the next run, and SHALL NOT update a standalone override. `sync` SHALL keep preserving the currently materialized revisions.

#### Scenario: Successful upgrade
- **WHEN** all selected sources refresh and the resulting installation succeeds
- **THEN** Powerspec commits additions, updates, and obsolete managed removals for the agent

#### Scenario: Upgrade fails before completion
- **WHEN** any required refresh or reconciliation step fails
- **THEN** Powerspec reports failure without committing obsolete-source removals

#### Scenario: Skill force does not repair hooks
- **WHEN** upgrade uses --force without --repair-hooks and finds a stale hook receipt
- **THEN** it reports hook reconciliation failure and preserves obsolete skills

#### Scenario: Authorized hook repair
- **WHEN** upgrade uses --repair-hooks and a valid stale receipt identifies hooks already matching the desired source
- **THEN** ownership is repaired through ZuAT, its recovery identifier is displayed, and upgrade continues after successful reconciliation

#### Scenario: Ambiguity despite repair option
- **WHEN** upgrade uses --repair-hooks but hook identity is unresolved
- **THEN** upgrade exits nonzero without claiming success or removing obsolete skills

### Requirement: Lifecycle commands expose active work while waiting

Init, including source-only init, and upgrade SHALL emit progress on stderr before potentially blocking work and report item outcomes as they occur, naming consumer setup, milkpan preparation, source identity and stage, skill identity and count, hooks, and selection publication or removal/recovery when reached. Source progress SHALL distinguish reuse of a validated selection, cache-eligible preparation and explicit refresh, reporting a download only when milkpan says content was fetched.

#### Scenario: Native source operation takes time
- **WHEN** init waits on milkpan to prepare a selected source
- **THEN** stderr identifies that source before the wait and continues reporting the active stage and elapsed waiting without requiring native output

#### Scenario: Earlier item fails
- **WHEN** one skill has a returned ownership conflict and later skills remain to be checked
- **THEN** the conflict is reported before the later checks finish, without claiming ownership or successful completion

#### Scenario: Source-only initialization
- **WHEN** init runs without an agent and prepares sources
- **THEN** source progress is visible without installing agent assets

#### Scenario: Redirected command output
- **WHEN** stdout and stderr are redirected to separate streams
- **THEN** readable progress remains on stderr and stdout retains only its existing results

#### Scenario: Existing selected source is reused
- **WHEN** init validates an existing consumer binding without acquisition
- **THEN** stderr reports retained selection reuse without suggesting materialization or a network refresh occurred

#### Scenario: A new consumer prepares a source
- **WHEN** init prepares a selection and milkpan reports that the content was already stored
- **THEN** progress reports reuse of stored content rather than a download

#### Scenario: Force requests refresh
- **WHEN** init --force starts a source operation
- **THEN** progress identifies the explicit refresh request and preserves normal waiting, failure, and stdout behavior

## REMOVED Requirements

### Requirement: First-use source preparation preserves existing stores
**Reason**: Saucepan's store initialization, installer leftovers and provider setup recovery no longer exist.
**Migration**: See "First-use preparation bootstraps Powerspec's own milkpan".

### Requirement: Doctor distinguishes executable checks from source readiness
**Reason**: Saucepan setup-status, raw-launcher migration and provider recovery guidance no longer exist.
**Migration**: See "Doctor distinguishes milkpan compatibility from source readiness".

## ADDED Requirements

### Requirement: First-use preparation bootstraps Powerspec's own milkpan

Source preparation SHALL bootstrap Powerspec's managed milkpan from the pinned, verified release in Powerspec's own milkpan home, never adopting, migrating or modifying another milkpan or Saucepan installation or store. It SHALL NOT replace credentials, delete store data, bypass guards or substitute test keys.

#### Scenario: Fresh machine
- **WHEN** no Powerspec milkpan home exists
- **THEN** preparation bootstraps and links the pinned milkpan before acquiring the selected sources

#### Scenario: Old Saucepan store present
- **WHEN** a Saucepan store and `saucepan-state.json` from an earlier Powerspec exist
- **THEN** preparation leaves them untouched and creates fresh milkpan selections

#### Scenario: Canonical GitHub source identity
- **WHEN** a recipe names an HTTPS GitHub repository with different owner/repository letter case or a `.git` suffix
- **THEN** it maps to the same canonical milkpan GitHub spec, while other parts of the reference stay distinct

#### Scenario: Credential or store failure stays an error
- **WHEN** milkpan reports a failure for the bucket or for GitHub credentials
- **THEN** source preparation reports an error and claims no success

#### Scenario: Upgrade does not replace missing initialization
- **WHEN** a consumer's sources were never initialized
- **THEN** upgrade does not silently perform that missing initialization

### Requirement: Doctor distinguishes milkpan compatibility from source readiness

Doctor SHALL label its successful milkpan observation as an executable compatibility check (protocol and version), without implying initialized selections. For the managed route it SHALL separately report whether the `milkpan` link exists and whether its lease matches the pinned release; an explicit override SHALL be labelled standalone. Results SHALL state these limitations without mutation.

#### Scenario: Compatible binary but no selected source
- **WHEN** doctor observes a compatible milkpan executable
- **THEN** its detail identifies executable compatibility, reports the managed link state separately when applicable, and states that selected-source readiness was not checked

#### Scenario: Managed link behind the pin
- **WHEN** the linked milkpan's lease does not match the pinned release
- **THEN** doctor reports that the next preparation or upgrade will switch it, without modifying anything

#### Scenario: Explicit standalone override
- **WHEN** the user selects an external milkpan through POWERSPEC_MILKPAN
- **THEN** doctor labels that selection standalone without checking managed state or changing the binary

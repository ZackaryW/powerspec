# Spec Delta

## MODIFIED Requirements

### Requirement: Initialization bootstraps the consumer and selected agent

`pspec init` SHALL locate the containing Git root, bootstrap OpenSpec without agent skills when needed, and establish `openspec/.pspec/config.toml`, ignored `current.toml`, and required directories. It SHALL accept an optional `--profile`, preserve compatible existing files and profile selection, support an empty selection that still activates global profiles, and SHALL prepare missing selected sources under the bounded shared-cache policy without refreshing existing consumer selections unless --force is supplied. Optional --agent SHALL provision that supported agent; omission SHALL prepare sources without installing skills/hooks or guessing an agent. Invalid agents SHALL fail before file effects. Later failures SHALL preserve completed setup and report incomplete bootstrap for retry.

#### Scenario: Initialize an empty Git repository
- **WHEN** a user runs `pspec init --profile @builtin/python-simple-cli` inside an uninitialized consumer
- **THEN** Powerspec creates the consumer structure and records the selected profile without provisioning an agent

#### Scenario: Initialize global profiles only
- **WHEN** a user runs `pspec init` without a profile in a Git repository
- **THEN** Powerspec creates an empty profile selection that allows global profiles to apply

#### Scenario: Repeat initialization
- **WHEN** initialization without --force is repeated for a compatible existing consumer
- **THEN** Powerspec preserves persistent and temporary values and reports the established consumer while reusing matching sources and requested agent installations

#### Scenario: Initialize with an agent
- **WHEN** a user runs pspec init --agent codex for a valid bundle
- **THEN** missing selected sources, profile-scoped skills, and user-level hooks are prepared without a separate install command

#### Scenario: Invalid agent
- **WHEN** init receives an unsupported agent
- **THEN** it reports the error before creating consumer files or acquiring sources

#### Scenario: Force initialization without an agent
- **WHEN** a user runs pspec init --force
- **THEN** all selected sources are explicitly refreshed and validated before selection publication, without installing agent assets or publishing contexts

#### Scenario: Force initialization with an agent
- **WHEN** a user runs pspec init --agent codex --force
- **THEN** sources are explicitly refreshed after any necessary provider-verified manager migration, then guarded provisioning permits source-matching owned hook receipt repair while preserving edited content and unrelated assets

#### Scenario: Discover the refresh override
- **WHEN** a user reads init help
- **THEN** --force is described as refreshing sources, authorizing verified migration of a supported unmanaged default manager when needed, and permitting guarded hook receipt repair for an explicitly selected agent


### Requirement: Lifecycle commands expose active work while waiting
Init, including source-only init, and upgrade SHALL emit default progress on stderr before potentially blocking work and report completed item outcomes as they occur. Source progress SHALL distinguish reuse of a validated consumer selection, cache-eligible source preparation, and explicitly requested refresh. It SHALL NOT report an actual shared-cache hit or download without provider evidence. Messages SHALL identify consumer setup, manager preparation, source identity and known stage, individual skill identity and known item count, hooks, and selection publication or removal/recovery when reached. The innermost active stage SHALL report elapsed waiting at five-second intervals during a blocked operation. Waiting SHALL NOT claim confirmed upstream activity, measured transfers or completion percentages. Successful results SHALL retain their stdout and exit contracts, and progress SHALL NOT activate for unrelated JSON or resolution protocols.

#### Scenario: Native source operation takes time
- **WHEN** init waits on Saucepan to prepare a selected source
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
- **WHEN** init requests preparation using the 24-hour cache policy and the provider exposes no hit or transfer telemetry
- **THEN** progress describes preparation with cache reuse allowed, without claiming either a hit or a download

#### Scenario: Force requests refresh
- **WHEN** init --force starts a source operation
- **THEN** progress identifies the explicit refresh request and preserves normal waiting, failure, and stdout behavior



### Requirement: First-use source preparation preserves existing stores
Source preparation SHALL delegate missing-store initialization and managed launcher publication to Saucepan through its official setup contract. Powerspec SHALL not publish the raw manager at the default launcher path or move existing installer leftovers. An unmanaged occupant SHALL require explicit Saucepan migration, authorized externally or through init --force, or an explicit standalone override; ordinary init and upgrade SHALL not supply migration consent. It SHALL NOT replace credentials, delete existing store data, bypass guards, or substitute test keys. Credential-service or damaged-store failures SHALL remain errors without a success claim. A failed or uncertain provider setup SHALL direct the user to inspect and explicitly resume the original provider operation where applicable, then rerun init with the same source options; upgrade SHALL NOT silently replace missing-only initialization.

#### Scenario: Fresh native store
- **WHEN** a store is absent and Saucepan permits initialization
- **THEN** Saucepan setup completes the managed installation before PowerSpec registers its resource-consumer application and continues acquisition

#### Scenario: Existing store cannot be initialized
- **WHEN** Saucepan rejects initialization because existing data or credential problems prevent it
- **THEN** PowerSpec reports failure without registering or acquiring sources or replacing store contents

#### Scenario: Failed binary-only setup
- **WHEN** the former installer left only recognized installer files under the default root
- **THEN** rerunning init preserves those files in place and reports the provider-supported manual preservation or separate-root prerequisite without moving them

#### Scenario: Canonical GitHub source identity
- **WHEN** Saucepan returns the same HTTPS GitHub repository with canonical lowercase owner/repository spelling and the normal .git suffix
- **THEN** source preparation accepts that identity while preserving host, transport, query, and reference distinctions; other hosts retain case-sensitive repository paths

### Requirement: Upgrade refreshes before committing removals

`pspec upgrade --agent <agent>` SHALL refresh selected Saucepan sources, compose the refreshed effective bundle, reconcile skills and hooks, and remove obsolete managed installations only after every required refresh and reconciliation step succeeds. The upgrade command SHALL reuse a compatible Saucepan installation and SHALL NOT implicitly self-update the shared manager; incompatibility SHALL report explicit provider update guidance before source refresh. `sync` SHALL continue to preserve the currently materialized revisions rather than refreshing them.

Upgrade SHALL accept `--repair-hooks` as separate explicit authorization to repair a valid stale hook ownership receipt when the uniquely identified native hooks already match the desired source. The existing `--force` option SHALL remain limited to selected skill replacement. Hook repair SHALL NOT authorize arbitrary hook replacement or bypass incomplete inspection. Failed reconciliation SHALL retain provider diagnostics and any recovery operation identifier; successful repair SHALL display its operation identifier. Ordinary initialization SHALL NOT authorize receipt repair. Init --force with an explicit agent SHALL authorize the same guarded receipt-only repair, without granting skill replacement or changing upgrade flag semantics.

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

## ADDED Requirements

### Requirement: Forced initialization authorizes bounded recovery
Init --force SHALL authorize provider-verified unmanaged-manager migration when selected sources require it and guarded hook receipt repair when an agent is explicit. It SHALL NOT authorize arbitrary asset replacement, manager self-update, or bypass provider preflight. Progress SHALL identify recovery operations and preserve their identifiers. Completed recovery effects SHALL remain accurately reported if later initialization fails.

#### Scenario: Forced init repairs a matching hook receipt
- **WHEN** init --agent codex --force encounters a valid owned stale receipt with a uniquely identified source-matching hook group
- **THEN** ZuAT performs guarded receipt-only repair, preserving native bytes and modification time, and init reports its operation identifier

#### Scenario: Hook content changes concurrently
- **WHEN** hooks cease to match the desired source between inspection and authorized repair
- **THEN** the provider rechecks source equality inside the operation and rejects repair without replacing those hooks

#### Scenario: Forced init cannot establish hook identity
- **WHEN** hook inspection is incomplete, identity is ambiguous, the receipt is invalid, or content is locally edited
- **THEN** forced initialization fails with diagnostics without positional overwrite or an installation fallback

#### Scenario: No agent is selected
- **WHEN** init --force runs without --agent
- **THEN** no native hooks are inspected or repaired and no agent is inferred

#### Scenario: Later source preparation fails after migration
- **WHEN** verified manager migration succeeds but a subsequent source operation fails
- **THEN** init reports overall failure and the completed migration separately, retaining provider backups and recovery evidence without claiming rollback

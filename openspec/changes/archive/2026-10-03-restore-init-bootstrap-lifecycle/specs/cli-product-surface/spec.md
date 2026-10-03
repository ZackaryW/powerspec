## MODIFIED Requirements

### Requirement: Initialization bootstraps the consumer and selected agent

`pspec init` SHALL locate the containing Git root, bootstrap OpenSpec without agent skills when needed, and establish `openspec/.pspec/config.toml`, ignored `current.toml`, and required directories. It SHALL accept an optional `--profile`, preserve compatible existing files and profile selection, support an empty selection that still activates global profiles, and SHALL prepare missing selected sources without refreshing existing materializations. Optional --agent SHALL provision that supported agent; omission SHALL prepare sources without installing skills/hooks or guessing an agent. Invalid agents SHALL fail before file effects. Later failures SHALL preserve completed setup and report incomplete bootstrap for retry.

#### Scenario: Initialize an empty Git repository
- **WHEN** a user runs `pspec init --profile @builtin/python-simple-cli` inside an uninitialized consumer
- **THEN** Powerspec creates the consumer structure and records the selected profile without provisioning an agent

#### Scenario: Initialize global profiles only
- **WHEN** a user runs `pspec init` without a profile in a Git repository
- **THEN** Powerspec creates an empty profile selection that allows global profiles to apply

#### Scenario: Repeat initialization
- **WHEN** initialization is repeated for a compatible existing consumer
- **THEN** Powerspec preserves persistent and temporary values and reports the established consumer while reusing matching sources and requested agent installations

#### Scenario: Initialize with an agent
- **WHEN** a user runs pspec init --agent codex for a valid bundle
- **THEN** missing selected sources, profile-scoped skills, and user-level hooks are prepared without a separate install command

#### Scenario: Invalid agent
- **WHEN** init receives an unsupported agent
- **THEN** it reports the error before creating consumer files or acquiring sources

### Requirement: Synchronization is local-aware and atomic

`pspec sync` SHALL compose bundled, consumer-local, and selected remote resources; resolve conditions against the owning consumer; validate every required selected resource; and only then atomically reconcile managed guidance in `openspec/config.yaml`. It SHALL preserve user-authored YAML and the original file when validation or publication fails, and SHALL acquire missing selected sources while reusing existing materializations without refresh. Successful acquisitions SHALL remain available if later validation fails; YAML publication remains atomic.

#### Scenario: Publish local and bundled contexts
- **WHEN** a consumer-local resource overrides or extends selected bundled guidance and all required resources are available
- **THEN** sync publishes the effective contributions once while preserving user-authored content

#### Scenario: Required source is unavailable
- **WHEN** a selected remote resource is not already materialized
- **THEN** sync attempts its first acquisition; a failure reports the unavailable resource and leaves `config.yaml` byte-for-byte unchanged

#### Scenario: Fresh machine
- **WHEN** selected sources have never been materialized
- **THEN** sync prepares Saucepan, acquires those sources, and publishes after complete validation

#### Scenario: Preserve current remote revision
- **WHEN** upstream has newer content than the current materialization
- **THEN** sync reuses the current revision; refreshing it requires upgrade

## REMOVED Requirements

### Requirement: Installation owns acquisition and agent reconciliation
**Reason**: Initialization owns bootstrap; the separate install command is removed.
**Migration**: Use pspec init --agent <agent> for provisioning, sync for missing-source acquisition and configuration reconciliation, and upgrade for refresh.

## ADDED Requirements

### Requirement: First-use source preparation preserves existing stores
Source preparation SHALL recognize missing native store secrets and missing indexes and delegate initialization to Saucepan. It SHALL NOT replace credentials, delete existing store data, bypass guards, or substitute test keys. Credential-service or damaged-store failures SHALL remain errors without a success claim.

#### Scenario: Fresh native store
- **WHEN** a missing secret is reported and Saucepan permits initialization
- **THEN** Powerspec initializes, registers its application, and continues acquisition

#### Scenario: Existing store cannot be initialized
- **WHEN** Saucepan rejects initialization because existing data or credential problems prevent it
- **THEN** Powerspec reports failure without registering or acquiring sources or replacing store contents

### Requirement: No separate install command
The public CLI SHALL expose agent bootstrap through init and SHALL NOT expose an install command. Help and bundled bootstrap guidance SHALL direct users to init --agent for provisioning.

#### Scenario: Discover setup command
- **WHEN** a user reads root and init help
- **THEN** init offers --agent and root help has no install command


## RENAMED Requirements

- FROM: `### Requirement: Initialization only establishes the consumer boundary`
- TO: `### Requirement: Initialization bootstraps the consumer and selected agent`

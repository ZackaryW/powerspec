# Cli Product Surface Specification

## Purpose

Provide a coherent Powerspec command lifecycle for establishing, inspecting, synchronizing, installing, upgrading, configuring, and resolving a Git-bounded OpenSpec consumer.

## Requirements

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

### Requirement: Status and doctor inspect without mutation

`pspec status` SHALL describe the owning consumer, selected profile or global-only mode, effective profiles after exclusions, selected contexts, traits, skills, sources, and pending installation facts without acquiring or modifying resources. `pspec doctor` SHALL check the consumer boundary and required external executables and integrations without repairing them. Both commands SHALL support human-readable output and `--json`.

#### Scenario: Inspect a configured consumer
- **WHEN** a user runs status inside a valid consumer
- **THEN** Powerspec reports the effective configuration and unresolved availability facts without changing files or installations

#### Scenario: Diagnose missing prerequisites
- **WHEN** doctor finds a missing or incompatible prerequisite
- **THEN** it reports a failed named check, exits nonzero, and makes no repair attempt

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

### Requirement: Upgrade refreshes before committing removals

`pspec upgrade --agent <agent>` SHALL refresh selected Saucepan sources, compose the refreshed effective bundle, reconcile skills and hooks, and remove obsolete managed installations only after every required refresh and reconciliation step succeeds. `sync` SHALL continue to preserve the currently materialized revisions rather than refreshing them.

#### Scenario: Successful upgrade
- **WHEN** all selected sources refresh and the resulting installation succeeds
- **THEN** Powerspec commits additions, updates, and obsolete managed removals for the agent

#### Scenario: Upgrade fails before completion
- **WHEN** any required refresh or reconciliation step fails
- **THEN** Powerspec reports failure without committing obsolete-source removals

### Requirement: Configuration and temporary state have explicit groups

`pspec config show` SHALL display persistent consumer configuration, `pspec config profile [PROFILE]` SHALL set or clear the selected profile while preserving other configuration, and `pspec config edit` SHALL open the owning persistent configuration in the user's configured editor. `pspec state show` SHALL display temporary global and change-scoped values, and `pspec state clear [--change CHANGE]` SHALL clear only the selected temporary scope while preserving persistent configuration. Read commands SHALL support `--json`.

#### Scenario: Change the selected profile
- **WHEN** a user sets or clears a profile through `config profile`
- **THEN** Powerspec updates only the persistent profile selector and leaves variables intact

#### Scenario: Clear one change
- **WHEN** a user runs `state clear --change example`
- **THEN** Powerspec removes only `_change.example` temporary values and preserves global temporary and all persistent values

### Requirement: Agent protocols live under resolve

`pspec resolve skill <name> --agent <agent>` SHALL preserve the existing Markdown-by-default and optional JSON skill protocol, including optional change-scoped inputs. `pspec resolve hook <event> --agent <agent>` SHALL preserve the generic hook-dispatch protocol and read native payload JSON from standard input. Protocol success SHALL write results to stdout; diagnostics SHALL use stderr and documented nonzero exit codes.

#### Scenario: Resolve supported skill content
- **WHEN** an agent requests a configured skill through `resolve skill`
- **THEN** Powerspec emits the resolved skill document in the requested representation

#### Scenario: Dispatch a native hook
- **WHEN** an installed agent callback invokes `resolve hook` with an event and native JSON payload
- **THEN** Powerspec resolves the nearest owning consumer and emits applicable hook guidance

### Requirement: Commands present stable human and JSON results

Human-facing lifecycle commands SHALL emit concise successful outcomes to stdout and actionable diagnostics to stderr. Commands that support `--json` SHALL emit exactly one JSON value on stdout and no human decoration. Operational failures SHALL exit nonzero and SHALL NOT emit a success claim.

#### Scenario: Request structured status
- **WHEN** a caller runs `pspec status --json`
- **THEN** stdout contains one parseable result object and diagnostics, if any, remain on stderr

#### Scenario: Operation fails
- **WHEN** a command cannot complete its promised effect
- **THEN** it exits nonzero and identifies the failed operation without a contradictory completion message

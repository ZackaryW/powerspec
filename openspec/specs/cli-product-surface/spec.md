# Cli Product Surface Specification

## Purpose

Provide a coherent Powerspec command lifecycle for establishing, inspecting, synchronizing, installing, upgrading, configuring, and resolving a Git-bounded OpenSpec consumer.

## Requirements

### Requirement: Initialization only establishes the consumer boundary

`pspec init` SHALL locate the containing Git root, bootstrap OpenSpec without agent skills when needed, and establish `openspec/.pspec/config.toml`, ignored `current.toml`, and required directories. It SHALL accept an optional `--profile`, preserve compatible existing files and profile selection, support an empty selection that still activates global profiles, and SHALL NOT acquire remote sources, install skills, or register hooks.

#### Scenario: Initialize an empty Git repository
- **WHEN** a user runs `pspec init --profile @builtin/python-simple-cli` inside an uninitialized consumer
- **THEN** Powerspec creates the consumer structure and records the selected profile without provisioning an agent

#### Scenario: Initialize global profiles only
- **WHEN** a user runs `pspec init` without a profile in a Git repository
- **THEN** Powerspec creates an empty profile selection that allows global profiles to apply

#### Scenario: Repeat initialization
- **WHEN** initialization is repeated for a compatible existing consumer
- **THEN** Powerspec preserves persistent and temporary values and reports the established consumer without reinstalling resources

### Requirement: Installation owns acquisition and agent reconciliation

`pspec install --agent <agent>` SHALL resolve the owning consumer, acquire configured selected sources that are not locally materialized, compose the effective bundle after exclusions, install the selected skills in the profile's declared scope for the named agent, and reconcile the generic Powerspec hook dispatcher for that agent. A failed item SHALL be reported without claiming complete installation, and a repeat invocation SHALL converge without duplicating managed resources.

#### Scenario: Install selected resources
- **WHEN** selected profiles reference bundled and Saucepan-managed skills and the user runs install for a supported agent
- **THEN** Powerspec acquires missing configured sources, provisions selected skills at their declared scope, and reconciles the dispatcher

#### Scenario: Repeat installation
- **WHEN** the installed resources already match the effective bundle
- **THEN** Powerspec reports unchanged or already available outcomes without duplicate installation

### Requirement: Status and doctor inspect without mutation

`pspec status` SHALL describe the owning consumer, selected profile or global-only mode, effective profiles after exclusions, selected contexts, traits, skills, sources, and pending installation facts without acquiring or modifying resources. `pspec doctor` SHALL check the consumer boundary and required external executables and integrations without repairing them. Both commands SHALL support human-readable output and `--json`.

#### Scenario: Inspect a configured consumer
- **WHEN** a user runs status inside a valid consumer
- **THEN** Powerspec reports the effective configuration and unresolved availability facts without changing files or installations

#### Scenario: Diagnose missing prerequisites
- **WHEN** doctor finds a missing or incompatible prerequisite
- **THEN** it reports a failed named check, exits nonzero, and makes no repair attempt

### Requirement: Synchronization is local-aware and atomic

`pspec sync` SHALL compose bundled, consumer-local, and already materialized remote resources; resolve conditions against the owning consumer; validate every required selected resource; and only then atomically reconcile managed guidance in `openspec/config.yaml`. It SHALL preserve user-authored YAML and the original file when validation or publication fails, and SHALL NOT acquire missing sources.

#### Scenario: Publish local and bundled contexts
- **WHEN** a consumer-local resource overrides or extends selected bundled guidance and all required resources are available
- **THEN** sync publishes the effective contributions once while preserving user-authored content

#### Scenario: Required source is unavailable
- **WHEN** a selected remote resource is not already materialized
- **THEN** sync reports the unavailable resource and leaves `config.yaml` byte-for-byte unchanged

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

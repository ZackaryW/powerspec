## MODIFIED Requirements

### Requirement: Initialization bootstraps the consumer and selected agent

`pspec init` SHALL locate the containing Git root, bootstrap OpenSpec without agent skills when needed, and establish `openspec/.pspec/config.toml`, ignored `current.toml`, and required directories. It SHALL accept an optional `--profile`, preserve compatible existing files and profile selection, support an empty selection that still activates global profiles, and SHALL prepare missing selected sources under the bounded shared-cache policy without refreshing existing consumer selections unless --force is supplied. Optional --agent SHALL provision that supported agent; omission SHALL prepare sources without installing skills/hooks or guessing an agent. Invalid agents SHALL fail before file effects. Later failures SHALL preserve completed setup and report incomplete bootstrap for retry.

A single `pspec init --agent <agent>` SHALL be sufficient to complete setup when selected skills exist as completely inspected unowned or locally modified copies. When both standard input and standard error are interactive terminals and --force is absent, init SHALL list those skills once, state that originals are backed up recoverably, and ask a single confirmation that defaults to no. Accepting SHALL replace them under the bounded replacement contract; declining SHALL leave them unchanged and report incomplete setup naming `pspec init --agent <agent> --force`. Without interactive terminals, init SHALL NOT prompt and SHALL report the same remedy.

Optional `--scope` SHALL accept `local`, `global` or `all`, defaulting to `all`. `local` SHALL establish the consumer and prepare and publish selected sources without inspecting or writing agent assets, and SHALL reject --agent. `global` SHALL require --agent, SHALL provision skills and hooks from existing published selections without acquiring, refreshing or publishing sources or rewriting consumer files, and SHALL fail with guidance to run a local or full init when a selection is missing. `all` SHALL perform both.

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

#### Scenario: Interactive init confirms conflict replacement
- **WHEN** a user runs pspec init --agent claude in an interactive terminal and selected skills exist as differing unowned copies
- **THEN** init installs non-conflicting skills, lists the conflicting skills, and asks once whether to replace them
- **AND** on acceptance the conflicts are recoverably replaced and init completes in the same invocation

#### Scenario: Interactive init declined
- **WHEN** the user declines the replacement confirmation
- **THEN** the conflicting copies are unchanged, init reports incomplete setup naming `pspec init --agent claude --force`, and published source selections remain usable by upgrade and sync

#### Scenario: Non-interactive init with conflicts
- **WHEN** init --agent runs without interactive terminals and selected skills conflict
- **THEN** init does not prompt, leaves the conflicts unchanged, and reports the --force remedy

#### Scenario: Invalid agent
- **WHEN** init receives an unsupported agent
- **THEN** it reports the error before creating consumer files or acquiring sources

#### Scenario: Force initialization without an agent
- **WHEN** a user runs pspec init --force
- **THEN** all selected sources are explicitly refreshed and validated before selection publication, without installing agent assets or publishing contexts

#### Scenario: Force initialization with an agent
- **WHEN** a user runs pspec init --agent codex --force
- **THEN** sources are explicitly refreshed after any necessary provider-verified manager migration, then guarded provisioning recoverably replaces completely inspected unowned or modified selected skills without prompting and permits source-matching owned hook receipt repair while preserving unrelated assets

#### Scenario: Local scope
- **WHEN** a user runs pspec init --scope local
- **THEN** the consumer and published source selections are established and no agent skills or hooks are inspected or written

#### Scenario: Global scope without selections
- **WHEN** a user runs pspec init --scope global --agent claude for a consumer with no published selection for a required source
- **THEN** init fails without acquiring sources and directs the user to run pspec init or pspec init --scope local

#### Scenario: Discover the refresh override
- **WHEN** a user reads init help
- **THEN** --force is described as refreshing sources, authorizing verified migration of a supported unmanaged default manager when needed, recoverably replacing conflicting selected skills, and permitting guarded hook receipt repair for an explicitly selected agent

### Requirement: Forced initialization authorizes bounded recovery
Init --force SHALL authorize provider-verified unmanaged-manager migration when selected sources require it, and, when an agent is explicit, guarded hook receipt repair and recoverable replacement of completely inspected unowned or locally modified selected skills. It SHALL NOT authorize replacement of incompletely inspected or unsupported skill targets, hook content replacement, manager self-update, or bypass provider preflight. Progress SHALL identify recovery operations and preserve their identifiers. Completed recovery effects SHALL remain accurately reported if later initialization fails.

#### Scenario: Forced init repairs a matching hook receipt
- **WHEN** init --agent codex --force encounters a valid owned stale receipt with a uniquely identified source-matching hook group
- **THEN** ZuAT performs guarded receipt-only repair, preserving native bytes and modification time, and init reports its operation identifier

#### Scenario: Forced init replaces a conflicting skill
- **WHEN** init --agent codex --force finds a completely inspected selected skill with differing unowned or modified content
- **THEN** ZuAT archives and replaces it and init reports the replacement and its operation identifier

#### Scenario: Hook content changes concurrently
- **WHEN** hooks cease to match the desired source between inspection and authorized repair
- **THEN** the provider rechecks source equality inside the operation and rejects repair without replacing those hooks

#### Scenario: Forced init cannot establish hook identity
- **WHEN** hook inspection is incomplete, identity is ambiguous, the receipt is invalid, or content is locally edited
- **THEN** forced initialization fails with diagnostics without positional overwrite or an installation fallback

#### Scenario: No agent is selected
- **WHEN** init --force runs without --agent
- **THEN** no native hooks or skills are inspected, repaired or replaced and no agent is inferred

#### Scenario: Later source preparation fails after migration
- **WHEN** verified manager migration succeeds but a subsequent source operation fails
- **THEN** init reports overall failure and the completed migration separately, retaining provider backups and recovery evidence without claiming rollback

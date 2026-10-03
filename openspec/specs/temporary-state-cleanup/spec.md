# Temporary State Cleanup Specification

## Purpose

Provide safe, scoped cleanup of gitignored runtime variables so completed work does not leak temporal decisions into later sessions.

## Requirements

### Requirement: Flush resolves the owning temporal store

`pspec flush` and `powerspec flush` SHALL resolve the nearest owning
`openspec/.pspec/config.toml` within the invocation's Git or worktree boundary
and SHALL operate only on its adjacent `current.toml`. They SHALL NOT discover a
consumer from the executable location or cross to a parent/sibling repository.

#### Scenario: Nested invocation
- **WHEN** flush is invoked below a configured consumer in a Git worktree
- **THEN** it targets that consumer's `openspec/.pspec/current.toml`

#### Scenario: No consumer
- **WHEN** no owning consumer exists within the Git boundary
- **THEN** flush reports a nonzero diagnostic and creates no state

### Requirement: Change-scoped flush preserves unrelated temporal values

When `--change <name>` is supplied, flush SHALL remove only the direct
`[_change.<name>]` variable layer. It SHALL preserve shared `[vars]`, every
other change layer, persistent `config.toml`, and unrelated TOML formatting or
comments. A missing file or absent named layer SHALL be an unchanged success.

#### Scenario: Archived change is removed
- **WHEN** current state contains shared values and multiple change layers and flush receives one existing change name
- **THEN** only that change layer is removed and the command reports an update

#### Scenario: Named change is already absent
- **WHEN** the requested change layer does not exist
- **THEN** flush reports unchanged without rewriting the file

### Requirement: Full flush establishes an empty temporal surface

When no change is supplied, flush SHALL clear every shared and change-specific
temporal variable and leave a valid canonical file containing an empty `[vars]`
table. A missing file SHALL be an unchanged success and SHALL NOT be created.

#### Scenario: Full reset
- **WHEN** current state contains any shared or change-specific values
- **THEN** flush atomically replaces it with the empty temporal surface

#### Scenario: Already empty
- **WHEN** current state already contains no temporal values
- **THEN** flush reports unchanged

### Requirement: Flush validates before atomic publication

Flush SHALL validate a present TOML document against the supported temporal
state shape before mutation. Parse, shape, staging, or replacement failures
SHALL preserve the original bytes and return a nonzero diagnostic without a
success message. Successful publication SHALL replace only `current.toml`.

#### Scenario: Malformed current state
- **WHEN** a present `current.toml` is invalid TOML or has an unsupported shape
- **THEN** flush fails and preserves its original bytes

#### Scenario: Archive cleanup handoff
- **WHEN** an OpenSpec archive succeeds and its workflow invokes `pspec flush --change <name>`
- **THEN** temporal values for that change are removed without changing persistent configuration

# CLI Scaffold Specification

## Purpose

Expose a discoverable Powerspec command surface before domain behavior exists, with honest diagnostics and no configuration or installation side effects.

## Requirements

### Requirement: Equivalent entrypoints expose command help

The installed `pspec` and `powerspec` commands SHALL expose the same commands and behavior. Root invocation without arguments and root `--help` SHALL show usage and the init, skill, hook, sync, and flush commands with exit status 0. Each command's `--help` SHALL describe its arguments and identify its placeholder status with exit status 0. Importing Powerspec or its CLI SHALL NOT execute a command or emit output.

#### Scenario: Discover commands
- **WHEN** either entrypoint is invoked without arguments or with --help
- **THEN** it displays command help successfully instead of the old greeting

#### Scenario: Inspect a command
- **WHEN** a user invokes skill --help without supplying a name or agent
- **THEN** help describes the required name and agent and optional change and JSON options without executing the placeholder

#### Scenario: Import the package
- **WHEN** a Python process imports powerspec or powerspec.cli
- **THEN** the import produces no output and runs no command

### Requirement: Placeholders distinguish unavailable behavior from success

Every syntactically valid placeholder invocation SHALL exit 1, write a diagnostic naming the command and stating it is not implemented to stderr, and leave stdout empty. This SHALL also apply to skill with --json; placeholders SHALL NOT return null, resolved guidance, pending choices, or a success payload.

#### Scenario: Request skill resolution
- **WHEN** pspec skill pspec-tdd --agent codex --change example --json is invoked
- **THEN** it reports skill is not implemented on stderr with exit status 1 and no stdout result

#### Scenario: Request configuration or lifecycle work
- **WHEN** init, sync, hook sessionStart, or flush --change example is invoked with valid syntax
- **THEN** it reports the selected operation is not implemented without claiming initialization, synchronization, dispatch, or cleanup

### Requirement: The scaffold validates command syntax

Skill SHALL require a positional name and --agent, accept optional --change and boolean --json; hook SHALL require a positional event. Init SHALL accept optional --agent and flush SHALL accept optional --change. Missing required arguments, unknown commands, and unknown options SHALL produce usage diagnostics with exit status 2 rather than entering a placeholder handler. These declarations SHALL NOT imply validation of domain-specific agent identities, change existence, or hook event support.

#### Scenario: Agent omitted
- **WHEN** skill pspec-tdd is invoked without --agent
- **THEN** parsing reports the missing option with exit status 2 instead of returning null or searching installations

#### Scenario: Invalid invocation
- **WHEN** an unknown command or option is supplied, or hook lacks its event
- **THEN** parsing reports a usage error with exit status 2

### Requirement: Scaffold commands have no domain side effects

Help, imports, syntax errors, and placeholder execution SHALL NOT create or modify consumer configuration, temporary runtime state, repository files, installed skills, or agent settings. The scaffold SHALL NOT perform network acquisition, installation, configuration discovery, or cleanup.

#### Scenario: Existing runtime choices survive flush placeholder
- **WHEN** flush --change example runs in a fixture containing persistent and temporary variables
- **THEN** all existing bytes remain unchanged and the command creates no domain files

#### Scenario: Empty repository stays empty
- **WHEN** init is invoked in an empty fixture directory
- **THEN** no OpenSpec, Powerspec, or agent installation directories are created

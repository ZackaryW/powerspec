## MODIFIED Requirements

### Requirement: Equivalent entrypoints expose command help

The installed `pspec` and `powerspec` commands SHALL expose the same commands and behavior. Root invocation without arguments and root `--help` SHALL show usage and the init, skill, hook, sync, flush, and upgrade commands with exit status 0. Each command's `--help` SHALL describe its arguments and identify whether the command remains a placeholder or implements its capability with exit status 0. Importing Powerspec or its CLI SHALL NOT execute a command or emit output.

#### Scenario: Discover commands
- **WHEN** either entrypoint is invoked without arguments or with --help
- **THEN** it displays command help successfully instead of the old greeting

#### Scenario: Inspect a command
- **WHEN** a user invokes skill --help without supplying a name or agent
- **THEN** help describes the required name and agent and optional change, selected-path evidence, and JSON options without executing domain behavior

#### Scenario: Import the package
- **WHEN** a Python process imports powerspec or powerspec.cli
- **THEN** the import produces no output and runs no command

### Requirement: Placeholders distinguish unavailable behavior from success

Every syntactically valid invocation of a command that remains a placeholder SHALL exit 1, name the command as not implemented on stderr, and leave stdout empty. Placeholders SHALL NOT emit null, resolved guidance, pending choices, or success payloads, including when a structured-output option is accepted. A command implemented under its capability specification SHALL follow that capability's result contract rather than report placeholder status. Each domain command SHALL become functional only under its own capability contract; readiness of skill SHALL NOT imply readiness of init, hook, sync, flush, or upgrade. Context synchronization is specified separately by implement-context-sync, and flush remains deferred.

#### Scenario: Request skill resolution
- **WHEN** pspec skill pspec-tdd --agent codex --change example --json is invoked after skill resolution is implemented
- **THEN** the command follows the skill-bootstrap and skill-content-resolution outcome contracts rather than the placeholder diagnostic

#### Scenario: Request configuration or lifecycle work
- **WHEN** a syntactically valid init, sync, hook sessionStart, or flush --change example invocation targets a still-unimplemented command
- **THEN** it reports the selected operation is not implemented with exit status 1 and empty stdout, without claiming initialization, synchronization, dispatch, or cleanup

### Requirement: Scaffold commands have no domain side effects

Help, imports, syntax errors, and placeholder execution SHALL NOT create or modify consumer configuration, temporary runtime state, repository files, installed skills, or agent settings. Scaffold-only paths SHALL NOT perform network acquisition, installation, configuration discovery, or cleanup. Implemented commands SHALL be governed by their capability-specific side-effect contracts; implementing one SHALL NOT enable side effects in help, imports, syntax errors, or remaining placeholders.

#### Scenario: Existing runtime choices survive flush placeholder
- **WHEN** flush --change example runs in a fixture containing persistent and temporary variables
- **THEN** all existing bytes remain unchanged and the command creates no domain files

#### Scenario: Empty repository stays empty
- **WHEN** init remains a placeholder and is invoked in an empty fixture directory
- **THEN** no OpenSpec, Powerspec, or agent installation directories are created

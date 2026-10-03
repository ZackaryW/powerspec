## MODIFIED Requirements

### Requirement: Equivalent entrypoints expose command help

The installed `pspec` and `powerspec` commands SHALL expose the same commands and behavior. Root invocation without arguments and root --help SHALL show usage and the init, skill, hook, sync, flush, and upgrade commands with exit status 0. Each command's --help SHALL describe its arguments and indicate its actual capability readiness with exit status 0. Sync help SHALL describe context reconciliation rather than claim placeholder status once implemented. Importing Powerspec or its CLI SHALL NOT execute a command or emit output.

#### Scenario: Discover commands
- **WHEN** either entrypoint is invoked without arguments or with --help
- **THEN** it displays command help successfully instead of the old greeting

#### Scenario: Inspect a command
- **WHEN** skill --help is invoked without supplying a name or agent
- **THEN** help describes the required name and agent and optional change and JSON options without executing domain behavior

#### Scenario: Inspect sync
- **WHEN** either alias invokes sync --help
- **THEN** it describes context reconciliation without reading or changing project configuration

#### Scenario: Import the package
- **WHEN** a Python process imports powerspec or powerspec.cli
- **THEN** the import produces no output and runs no command

### Requirement: Placeholders distinguish unavailable behavior from success

Every syntactically valid invocation of a command that remains a placeholder SHALL exit 1, name the command as not implemented on stderr, and leave stdout empty. This SHALL apply to structured-output options on remaining placeholders; they SHALL NOT emit null, resolved guidance, pending choices, or success payloads. Implemented commands SHALL follow their capability contracts. Sync SHALL follow context-sync rather than report unavailable behavior once this change is implemented. Implementing sync SHALL NOT enable init, skill, hook, flush, or upgrade unless their own capability changes have been implemented.

#### Scenario: Request skill resolution
- **WHEN** skill resolution remains unimplemented and pspec skill pspec-tdd --agent codex --change example --json is invoked
- **THEN** it reports unavailable behavior with nonzero status and no success payload

#### Scenario: Request configuration or lifecycle work
- **WHEN** an invocation targets a domain command that still remains unimplemented
- **THEN** it reports that operation as not implemented with exit status 1 and empty stdout

#### Scenario: Synchronize contexts
- **WHEN** sync is invoked after context reconciliation is implemented
- **THEN** it follows context-sync's updated, unchanged, or failure contract rather than the placeholder diagnostic

### Requirement: Scaffold commands have no domain side effects

Help, imports, syntax errors, and placeholder execution SHALL NOT create or modify consumer configuration, temporal state, repository files, installed skills, or agent settings. Scaffold-only paths SHALL NOT perform acquisition, installation, configuration discovery, or cleanup. Implemented commands SHALL use their capability side-effect contracts; sync SHALL modify only its owning config.yaml as specified by context-sync. Implementing sync SHALL NOT introduce side effects in help, imports, syntax failures, or remaining placeholders.

#### Scenario: Existing runtime choices survive flush placeholder
- **WHEN** flush --change example remains a placeholder and runs with existing variable files
- **THEN** all existing bytes remain unchanged and no domain files are created

#### Scenario: Empty repository stays empty
- **WHEN** init remains a placeholder and is invoked in an empty fixture directory
- **THEN** no OpenSpec, Powerspec, or agent installation directories are created

#### Scenario: Sync help leaves files unchanged
- **WHEN** sync --help runs inside a configured consumer
- **THEN** it performs no configuration discovery or publication and preserves all files

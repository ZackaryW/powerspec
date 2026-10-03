## MODIFIED Requirements

### Requirement: Equivalent entrypoints expose command help

The installed `pspec` and `powerspec` commands SHALL expose the same commands and behavior. Root invocation without arguments and root `--help` SHALL show usage and the init, skill, hook, sync, flush, and upgrade commands with exit status 0. Each command's `--help` SHALL describe its arguments and identify whether the command remains a placeholder or implements its capability with exit status 0. Importing Powerspec or its CLI SHALL NOT execute a command or emit output.

#### Scenario: Discover commands
- **WHEN** either entrypoint is invoked without arguments or with --help
- **THEN** it displays command help successfully instead of the old greeting

#### Scenario: Inspect a command
- **WHEN** a user invokes skill --help without supplying a name or agent
- **THEN** help describes the required name and agent and optional change and JSON options without executing domain behavior

#### Scenario: Import the package
- **WHEN** a Python process imports powerspec or powerspec.cli
- **THEN** the import produces no output and runs no command

#### Scenario: Inspect upgrade
- **WHEN** either alias invokes upgrade --help
- **THEN** help describes the required target agent and exits 0 without acquiring sources or changing installations

### Requirement: The scaffold validates command syntax

Skill SHALL require a positional name and --agent, accept optional --change and boolean --json; hook SHALL require a positional event. Init SHALL accept optional --agent and flush SHALL accept optional --change. Upgrade SHALL require --agent and accept no positional arguments. Missing required arguments, unknown commands, and unknown options SHALL produce usage diagnostics with exit status 2 rather than entering a handler. These declarations SHALL NOT imply validation of domain-specific agent identities, change existence, or hook event support.

#### Scenario: Agent omitted
- **WHEN** skill pspec-tdd is invoked without --agent
- **THEN** parsing reports the missing option with exit status 2 instead of returning null or searching installations

#### Scenario: Invalid invocation
- **WHEN** an unknown command or option is supplied, or hook lacks its event
- **THEN** parsing reports a usage error with exit status 2

#### Scenario: Upgrade agent omitted
- **WHEN** upgrade is invoked without --agent
- **THEN** parsing reports the missing option with exit status 2 without refreshing sources, installing resources, or committing removals

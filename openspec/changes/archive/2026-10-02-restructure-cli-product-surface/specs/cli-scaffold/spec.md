# CLI Scaffold Specification Delta

## ADDED Requirements

### Requirement: Equivalent entrypoints expose the product command surface

The installed `pspec` and `powerspec` commands SHALL expose the same commands and behavior. Root invocation without arguments and root `--help` SHALL show the human control-plane commands `init`, `status`, `sync`, `install`, `upgrade`, `doctor`, and `config`, plus the grouped `state` and `resolve` commands, with exit status 0. Importing Powerspec or its CLI SHALL NOT execute a command or emit output.

#### Scenario: Discover the control plane
- **WHEN** either entrypoint is invoked without arguments or with `--help`
- **THEN** it displays the same organized command surface successfully

#### Scenario: Import the package
- **WHEN** a Python process imports `powerspec` or `powerspec.cli`
- **THEN** the import produces no output and runs no command

### Requirement: Command help and syntax validation are side-effect free

Every command and command group SHALL provide help without requiring operational arguments. Missing required arguments, unknown commands, and unknown options SHALL produce usage diagnostics with exit status 2. Help, imports, and syntax errors SHALL NOT create consumer files, acquire sources, install skills, register hooks, or alter temporary state.

#### Scenario: Inspect a nested command
- **WHEN** a user invokes `resolve skill --help`, `config profile --help`, or `state clear --help`
- **THEN** Powerspec describes that command without executing it

#### Scenario: Reject invalid syntax
- **WHEN** a required argument is omitted or an unknown option is supplied
- **THEN** Powerspec emits a usage diagnostic with exit status 2 and makes no domain changes

### Requirement: Compatibility aliases remain callable but undiscoverable

The historical `skill`, `hook`, and `flush` commands SHALL remain behaviorally equivalent to `resolve skill`, `resolve hook`, and `state clear` respectively during migration, but SHALL NOT appear in root help.

#### Scenario: Existing automation invokes an alias
- **WHEN** a caller uses `skill`, `hook`, or `flush` with valid arguments
- **THEN** Powerspec executes the corresponding grouped command with the same output and exit status

## REMOVED Requirements

### Requirement: Equivalent entrypoints expose command help
**Reason**: The historical command list no longer represents the implemented product surface.
**Migration**: Use the replacement equivalent-entrypoints requirement above and the grouped command help.

### Requirement: Placeholders distinguish unavailable behavior from success
**Reason**: The commands are implemented and no longer placeholders.
**Migration**: Rely on each command's documented success, diagnostic, and exit-status contract.

### Requirement: The scaffold validates command syntax
**Reason**: Syntax now covers the complete grouped product surface rather than the original scaffold.
**Migration**: Use the replacement command-help and syntax-validation requirement above.

### Requirement: Scaffold commands have no domain side effects
**Reason**: Operational commands intentionally perform domain effects, while help, imports, and syntax errors remain side-effect free.
**Migration**: Use the replacement side-effect-free help and syntax requirement above and each lifecycle command's explicit effect contract.

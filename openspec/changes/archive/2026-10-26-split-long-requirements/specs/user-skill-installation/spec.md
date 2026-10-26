## MODIFIED Requirements

### Requirement: Installation targets the explicitly identified agent at the declared scope

Initialization with --agent SHALL provision effective profile skills through ZuAT for the explicitly identified agent at each declaring profile's scope. Project scope SHALL require the repository root as explicit project_root, and bundled OpenSpec skills SHALL default to user scope. Initialization SHALL NOT guess installed agents or switch scope when the requested one is unavailable. The global builtin profile SHALL contribute pspec-skill-bootstrap unless excluded.

#### Scenario: Initialize a Python CLI project
- **WHEN** the user initializes the project with the reviewed user-scoped Python CLI and builtin profiles for an identified supported agent
- **THEN** OpenSpec, bootstrap, and TDD skills are provisioned to that agent's user-level surface through ZuAT
- **AND** BDD is not selected by that bundle

#### Scenario: Target scope is unsupported
- **WHEN** the selected agent cannot accept the requested scope, or a project installation lacks explicit project context
- **THEN** initialization reports the limitation without silently switching installation scope

#### Scenario: First-run profile selection
- **WHEN** a fresh consumer runs `pspec init --agent <agent> --profile <qualified-reference>`
- **THEN** initialization validates the agent and profile selection before writing, persists the selected profile in config.toml, then validates and provisions the effective bundle; later failures preserve established consumer files for retry
- **AND** later runs reuse the configured selection; a conflicting --profile is diagnosed without replacing it

#### Scenario: No selected profile
- **WHEN** neither --profile nor existing consumer configuration selects a profile and --agent identifies the target
- **THEN** init composes and provisions the global profiles after consumer exclusions
- **AND** no selected-profile defaults or contributions are added; empty profile selection remains valid on later sync and runtime resolution

#### Scenario: Agent omitted
- **WHEN** initialization has no --agent
- **THEN** it prepares the consumer and selected sources without installing skills or hooks and explains how to request agent provisioning

#### Scenario: Plan exposes targets before completion
- **WHEN** initialization provisions an agent
- **THEN** the selected resource identities and their targets are reported before completion is reported

### Requirement: Repository skill installation requires profile project scope

Initialization SHALL establish the Git-root OpenSpec/Powerspec configuration boundary, and OpenSpec repository bootstrap SHALL disable its local skill generation. Powerspec SHALL create repository-local native skills through ZuAT only for project-scoped profiles; user-scoped profiles SHALL NOT create local copies. Source resources under .pspec/skills SHALL remain authoring inputs, not evidence of installation, and existing repository skill files SHALL be preserved rather than removed.

#### Scenario: Fresh repository
- **WHEN** initialization creates OpenSpec configuration in a new repository with only user-scoped profiles
- **THEN** it creates no project-local agent skill installation and reports user-level provisioning separately

#### Scenario: Development checkout has source skills
- **WHEN** a checkout contains bundled skill source folders or pre-existing agent skill files
- **THEN** initialization preserves them and does not claim their presence alone establishes the requested managed installation

#### Scenario: Project-scoped profile installs locally
- **WHEN** a project-scoped profile contributes a skill
- **THEN** ZuAT installs it at the repository-local native skill location

### Requirement: Provisioning is repeatable and reports partial failures

Matching installed resources SHALL be reused, and conflicting unmanaged or locally modified targets SHALL be reported rather than silently overwritten. Repeated initialization SHALL preserve project configuration and unrelated user-level resources. Partial failures SHALL identify completed and failed actions without claiming rollback or successful completion of the whole bundle. Skill lookup SHALL never perform repair installation implicitly.

#### Scenario: Repeated initialization
- **WHEN** the selected skills at their declared scopes already match the requested versions
- **THEN** initialization avoids redundant replacement and preserves project values

#### Scenario: Partial installation
- **WHEN** OpenSpec skill provisioning succeeds but a profile skill fails
- **THEN** the result reports both outcomes and does not claim the bundle is ready or undo unrelated installations

#### Scenario: Lookup never repairs
- **WHEN** skill lookup finds a missing or damaged installation
- **THEN** it reports the state without installing or repairing anything

#### Scenario: Explicit replacement during upgrade
- **WHEN** a selected skill already exists with differing unowned content and the user runs `pspec upgrade --agent <agent> --force`
- **THEN** Powerspec asks ZuAT to archive and replace that selected target and reports the resulting action
- **AND** ordinary upgrade continues to preserve the same target as a conflict

#### Scenario: Explicit replacement during forced init
- **WHEN** a selected skill already exists with differing unowned or locally modified content and the user runs `pspec init --agent <agent> --force`
- **THEN** Powerspec asks ZuAT to archive and replace that selected target and reports the resulting action and its recovery operation

#### Scenario: Conflict names its remedy
- **WHEN** a completely inspected selected skill remains an unowned or modified conflict without replacement authorization
- **THEN** its failure diagnostic names `pspec init --agent <agent> --force` as the command that authorizes recoverable replacement

#### Scenario: Incomplete inspection is never forced
- **WHEN** replacement is authorized but a target's inspection is incomplete or unsupported
- **THEN** that target fails with its diagnostics and is not replaced

### Requirement: Bundle a pinned OpenSpec skill snapshot for local provisioning

Maintainer preparation SHALL vendor selected committed OpenSpec skill directories from a pinned compatible upstream revision, with complete resources, upstream license, and repository/commit/path provenance, and Powerspec SHALL bundle them through Hatchling in its wheel and sdist. Ordinary builds, sdist builds and pspec init SHALL NOT fetch upstream OpenSpec or run its skill generation. uv SHALL remain usable as the build frontend, preserving the reviewed uv run pytest default.

#### Scenario: Build a wheel from the source distribution
- **WHEN** Powerspec is built offline from its sdist with build dependencies already available
- **THEN** the wheel includes the same selected skill resources, license, and provenance without accessing a maintainer checkout

#### Scenario: uv remains the frontend
- **WHEN** a maintainer builds or tests Powerspec through uv
- **THEN** the build succeeds and uv run pytest keeps its reviewed default behavior

#### Scenario: Install bundled OpenSpec skills without upstream access
- **WHEN** pspec init provisions selected OpenSpec skills from an installed Powerspec distribution with no upstream repository or saucepan cache available
- **THEN** ZuAT receives complete local package resources without attempting an OpenSpec download or generation

#### Scenario: Missing bundled resource
- **WHEN** a required selected OpenSpec skill is absent from the package
- **THEN** provisioning reports the missing resource rather than fetching a replacement or claiming success

## ADDED Requirements

### Requirement: Initialization ignores only temporary consumer state

Initialization SHALL establish a Git ignore rule for the consumer's current.toml without ignoring config.toml or the whole consumer directory, and both files SHALL accept the same shared/change variable table structure. Existing ignore rules SHALL be preserved, and ignoring a file SHALL NOT be presented as untracking an already tracked file.

#### Scenario: Only current.toml is ignored
- **WHEN** initialization establishes a consumer
- **THEN** Git ignores current.toml while config.toml and the consumer directory stay trackable

#### Scenario: Existing ignore rules are preserved
- **WHEN** the consumer's ignore file already contains other rules
- **THEN** initialization keeps them and adds only what is needed to ignore current.toml

#### Scenario: current.toml is already tracked
- **WHEN** current.toml is already tracked by Git
- **THEN** initialization warns that the ignore rule does not untrack it

### Requirement: Skill replacement requires explicit authorization

`pspec upgrade --force`, `pspec init --agent <agent> --force`, or an accepted interactive init confirmation SHALL permit ZuAT to recoverably replace selected unowned or modified skill targets after complete inspection, never bypassing incomplete inspection, unsupported targets, source validation, hook ownership or obsolete-skill removal safeguards. Without it, an exact unowned copy MAY be adopted unchanged, while a differing copy SHALL remain a conflict that names its remedy.

#### Scenario: Exact unowned copy is adopted
- **WHEN** a completely inspected unowned copy is byte-identical to the selected resource and no replacement is authorized
- **THEN** ZuAT records ownership without rewriting its bytes

### Requirement: Bundled OpenSpec skills provision from the installed package

ZuAT SHALL provision bundled OpenSpec resources from the installed Powerspec package at their declaring profile's scope, defaulting to user scope, without requiring a .pspec catalog, developer cache paths, or a registered remote source. Missing packaged resources or known incompatible versions SHALL be reported rather than fetched, generated or partially installed. Saucepan SHALL remain the acquisition mechanism only for user-added remote sources.

#### Scenario: Incompatible bundled version
- **WHEN** a packaged OpenSpec resource is known to be incompatible
- **THEN** provisioning reports it instead of installing it or falling back to remote fetching

# User Skill Installation Specification

## Purpose

Provision complete packaged OpenSpec and profile skills for an explicit agent at profile-defined scopes while establishing a repeatable repository consumer.

## Requirements

### Requirement: Installation targets the explicitly identified agent at the declared scope

Powerspec initialization with --agent SHALL provision effective profile skills through ZuAT for the explicitly identified target agent using each declaring profile's scope. Project scope SHALL require the target repository root as explicit project_root. Bundled OpenSpec skills SHALL retain user scope by default. Initialization SHALL NOT guess all installed agents or switch between user and project scope when the requested scope is unavailable. The global builtin profile SHALL contribute pspec-skill-bootstrap unless excluded. The installation plan SHALL expose selected resource identities and targets before reporting completion.

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

### Requirement: Repository skill installation requires profile project scope

Initialization SHALL establish the Git-root OpenSpec/Powerspec configuration boundary. OpenSpec repository bootstrap SHALL disable its local skill generation. Powerspec SHALL create repository-local native skill installations through ZuAT only for skills contributed by project-scoped profiles; user-scoped profiles SHALL NOT create local skill copies. Existing source resources under .pspec/skills SHALL remain authoring inputs, not evidence of native installation. Existing repository skill files SHALL be preserved rather than removed as cleanup. Initialization SHALL establish a Git ignore rule for the consumer's current.toml without ignoring config.toml or the whole consumer directory. Both files SHALL accept the same shared/change variable table structure. Existing ignore rules SHALL be preserved; ignoring a file SHALL NOT be presented as untracking an already tracked file.

#### Scenario: Fresh repository
- **WHEN** initialization creates OpenSpec configuration in a new repository with only user-scoped profiles
- **THEN** it creates no project-local agent skill installation and reports user-level provisioning separately

#### Scenario: Development checkout has source skills
- **WHEN** a checkout contains bundled skill source folders or pre-existing agent skill files
- **THEN** initialization preserves them and does not claim their presence alone establishes the requested managed installation

### Requirement: Install complete supported skill resources

ZuAT provisioning SHALL preserve the skill entrypoint, pspec.toml when present, and all referenced content resources needed for later branch selection. It SHALL not prune installation to the branch currently selected in one repository. Ordinary OpenSpec skills without manifests SHALL remain usable through null fallback. Lookup SHALL use the target agent's installed identity and content, with conflicts or missing installations reported explicitly.

#### Scenario: Later language selection changes
- **WHEN** another project invokes a different supported branch of an already installed skill
- **THEN** its resources remain available without reinstalling for each invocation

#### Scenario: Unsupported ordinary skill
- **WHEN** an installed OpenSpec skill has no Powerspec manifest
- **THEN** lookup returns null and its complete normal entrypoint remains available

### Requirement: Provisioning is repeatable and reports partial failures

Matching installed resources SHALL be reused. Conflicting unmanaged or locally modified targets SHALL be reported rather than silently overwritten. Repeated initialization SHALL preserve project configuration and unrelated user-level resources. Partial provisioning failures SHALL identify completed and failed actions without claiming rollback or successful completion of the whole bundle. Skill lookup SHALL never perform repair installation implicitly.

An explicit `pspec upgrade --force` SHALL permit ZuAT to recoverably replace selected unowned or locally modified skill targets after complete inspection. It SHALL NOT bypass incomplete inspection, unsupported targets, source validation, hook ownership checks, or obsolete-skill removal safeguards. Without `--force`, an exact unowned copy MAY be adopted without rewriting its bytes, while a differing unowned or modified copy SHALL remain a conflict.

#### Scenario: Repeated initialization
- **WHEN** the selected skills at their declared scopes already match the requested versions
- **THEN** initialization avoids redundant replacement and preserves project values

#### Scenario: Partial installation
- **WHEN** OpenSpec skill provisioning succeeds but a profile skill fails
- **THEN** the result reports both outcomes and does not claim the bundle is ready or undo unrelated installations

#### Scenario: Explicit replacement during upgrade
- **WHEN** a selected skill already exists with differing unowned content and the user runs `pspec upgrade --agent <agent> --force`
- **THEN** Powerspec asks ZuAT to archive and replace that selected target and reports the resulting action
- **AND** ordinary upgrade continues to preserve the same target as a conflict

### Requirement: Bundle a pinned OpenSpec skill snapshot for local provisioning

Maintainer preparation SHALL vendor selected committed OpenSpec skill directories from a pinned compatible upstream revision, retaining complete selected resources, upstream license, and repository/commit/path provenance. Powerspec SHALL bundle them through Hatchling in its wheel and source distribution. Ordinary builds, builds from the sdist, and pspec init SHALL NOT fetch the upstream OpenSpec repository or run upstream skill generation. ZuAT SHALL provision the selected resources from the installed Powerspec package at their declaring profile's scope, with user scope as the bundled OpenSpec default. uv SHALL remain usable as the environment/build frontend, and the reviewed uv run pytest default SHALL be preserved.

The upstream resources SHALL NOT require a .pspec catalog, developer-specific cache paths, or a registered remote source for installation. Missing packaged resources or known incompatible versions SHALL be reported rather than silently falling back to remote fetching, generation, or incomplete installation. Saucepan SHALL remain the acquisition mechanism for user-added remote sources; that capability is separate from provisioning these bundled dependencies.

#### Scenario: Install bundled OpenSpec skills without upstream access
- **WHEN** pspec init provisions selected OpenSpec skills from an installed Powerspec distribution with no upstream repository or saucepan cache available
- **THEN** ZuAT receives complete local package resources without attempting an OpenSpec download or generation

#### Scenario: Build a wheel from the source distribution
- **WHEN** Powerspec is built offline from its sdist with build dependencies already available
- **THEN** the wheel includes the same selected skill resources, license, and provenance without accessing a maintainer checkout

#### Scenario: Missing bundled resource
- **WHEN** a required selected OpenSpec skill is absent from the package
- **THEN** provisioning reports the missing resource rather than fetching a replacement or claiming success

### Requirement: Distinguish resource selection from native availability

Powerspec SHALL distinguish selecting guidance or excluding a profile from installing/removing a user-level skill. The ZuAT integration SHALL use verified install, uninstall, update, and restore capabilities without claiming a universal native skill enable/disable operation. ZuAT artifact policy SHALL NOT be represented as native agent activation control. Excluding a project profile SHALL NOT implicitly uninstall shared user-level skills or claim those skills are undiscoverable to the agent.

#### Scenario: Profile exclusion preserves shared installation
- **WHEN** one project excludes a profile whose skills remain installed for other projects
- **THEN** Powerspec removes that profile's contributions for the consumer without removing the native skill or claiming to disable it in the host

## MODIFIED Requirements

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

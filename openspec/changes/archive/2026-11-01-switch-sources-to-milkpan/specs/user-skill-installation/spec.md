# Spec Delta

## MODIFIED Requirements

### Requirement: Bundle a pinned OpenSpec skill snapshot for local provisioning

Maintainer preparation SHALL vendor selected committed OpenSpec skill directories from a pinned compatible upstream revision, with complete resources, upstream license, and repository/commit/path provenance, and Powerspec SHALL bundle them through Hatchling in its wheel and sdist. Ordinary builds, sdist builds and pspec init SHALL NOT fetch upstream OpenSpec or run its skill generation. uv SHALL remain usable as the build frontend, preserving the reviewed uv run pytest default.

#### Scenario: Build a wheel from the source distribution
- **WHEN** Powerspec is built offline from its sdist with build dependencies already available
- **THEN** the wheel includes the same selected skill resources, license, and provenance without accessing a maintainer checkout

#### Scenario: uv remains the frontend
- **WHEN** a maintainer builds or tests Powerspec through uv
- **THEN** the build succeeds and uv run pytest keeps its reviewed default behavior

#### Scenario: Install bundled OpenSpec skills without upstream access
- **WHEN** pspec init provisions selected OpenSpec skills from an installed Powerspec distribution with no upstream repository or milkpan bucket available
- **THEN** ZuAT receives complete local package resources without attempting an OpenSpec download or generation

#### Scenario: Missing bundled resource
- **WHEN** a required selected OpenSpec skill is absent from the package
- **THEN** provisioning reports the missing resource rather than fetching a replacement or claiming success

### Requirement: Bundled OpenSpec skills provision from the installed package

ZuAT SHALL provision bundled OpenSpec resources from the installed Powerspec package at their declaring profile's scope, defaulting to user scope, without requiring a .pspec catalog, developer cache paths, or a registered remote source. Missing packaged resources or known incompatible versions SHALL be reported rather than fetched, generated or partially installed. Milkpan SHALL remain the acquisition mechanism only for user-added remote sources.

#### Scenario: Incompatible bundled version
- **WHEN** a packaged OpenSpec resource is known to be incompatible
- **THEN** provisioning reports it instead of installing it or falling back to remote fetching

# Package Distribution Specification

## Purpose

Provide reproducible bundled external resources without maintaining duplicate authoring copies.

## Requirements

### Requirement: External packaged resources have one pinned build source

Externally maintained skills bundled with Powerspec SHALL be declared as an immutable upstream source with selected paths, not committed as duplicate catalog copies. Building the source distribution SHALL materialize and validate that declaration and SHALL fail rather than emit a partial catalog. The source distribution SHALL carry the resolved snapshot so its wheel builds offline with the same resources, and installed commands SHALL read packaged resources without contacting upstream.

#### Scenario: Build resolves the declared OpenSpec skills
- **WHEN** a release source distribution is built from a checkout containing the pinned OpenSpec build-source declaration
- **THEN** the artifact contains the selected complete skills, license, and exact revision provenance without requiring tracked duplicate skill directories

#### Scenario: Declared source cannot be reproduced
- **WHEN** the pinned revision or selected skill paths cannot be acquired and validated
- **THEN** the build fails without publishing a partial or differently sourced catalog

#### Scenario: Declared resource is invalid
- **WHEN** a selected resource is missing, a skill root is invalid, the revision does not match, or a selected path escapes the source
- **THEN** the build fails without emitting a partial catalog

#### Scenario: Materialized paths are deterministic
- **WHEN** the same declaration is materialized for two builds
- **THEN** both produce the same packaged resource paths with the upstream license and revision provenance

#### Scenario: Wheel is rebuilt from the source distribution
- **WHEN** a wheel is built offline from the completed source distribution
- **THEN** it contains the same builtin resource paths and content as the wheel built from the reviewed checkout

#### Scenario: Installed runtime uses the packaged snapshot
- **WHEN** an installed Powerspec command resolves a builtin OpenSpec skill
- **THEN** it reads the packaged snapshot without contacting the upstream repository or requiring a development checkout

### Requirement: Bundled workflows have an explicit CLI compatibility floor

Powerspec SHALL document and enforce OpenSpec 1.14.3 or later for fresh OpenSpec bootstrap. The floor SHALL be the oldest CLI release compatible with the bundled workflow skills and Powerspec's own OpenSpec invocations, and SHALL be raised only when one of them depends on newer CLI behavior. Doctor SHALL report an older CLI as incompatible. Rejection SHALL precede OpenSpec initialization and SHALL NOT upgrade the CLI or replace existing consumer configuration.

#### Scenario: Older CLI cannot bootstrap
- **WHEN** fresh bootstrap discovers OpenSpec 1.14.2 or an earlier version
- **THEN** it reports the required minimum version without invoking initialization or creating consumer files

#### Scenario: Compatible CLI initializes without local agent tools
- **WHEN** fresh bootstrap discovers OpenSpec 1.14.3 or a newer compatible version
- **THEN** it initializes OpenSpec with native agent-tool generation disabled, preserving Powerspec's skill provisioning boundary

#### Scenario: Floor older than the bundled snapshot
- **WHEN** Powerspec bundles the v1.15.0 workflow skills and fresh bootstrap discovers OpenSpec 1.14.3
- **THEN** bootstrap proceeds and doctor reports the CLI as compatible

#### Scenario: Documentation separates snapshot and floor
- **WHEN** a user reads Powerspec's compatibility documentation
- **THEN** it states the bundled snapshot release and the CLI floor separately

#### Scenario: Doctor reports compatibility without mutation
- **WHEN** doctor inspects an older OpenSpec CLI
- **THEN** it reports a failed compatibility check naming 1.14.3 without installing or updating software

# Spec Delta

## Purpose

Provide a reproducible Powerspec distribution that installs from versioned Python artifacts without requiring Git checkouts or mutable source-host availability.

## ADDED Requirements

### Requirement: Runtime dependencies resolve from versioned package artifacts

Published Powerspec distributions SHALL declare compatible released versions of Saucepan SDK, ZuAT, and Zuu through a configured Python package index. Published metadata SHALL NOT require Git URL dependencies. Each dependency range SHALL have an explicit compatibility boundary tested by the Powerspec release workflow.

#### Scenario: Install the published tool
- **WHEN** a user installs a released Powerspec version from its configured package index
- **THEN** the installer resolves versioned wheel or source artifacts without invoking Git or cloning a dependency repository

#### Scenario: Compatible dependency is unavailable
- **WHEN** a required compatible package artifact is absent from configured indexes
- **THEN** installation fails with the missing package requirement instead of fetching an undeclared Git source

### Requirement: Release builds exclude development source overrides

The release workflow SHALL build Powerspec with development source overrides disabled, inspect the resulting metadata for direct VCS requirements, and install the produced artifact in a clean isolated environment before publication. Publication SHALL stop if the artifact depends on an undeclared source checkout or the installed command cannot complete its smoke checks.

#### Scenario: Source override leaks into metadata
- **WHEN** a release candidate contains a direct Git or local-path runtime requirement
- **THEN** release verification fails before publication

#### Scenario: Wheel smoke test
- **WHEN** a wheel is built from the release candidate
- **THEN** a clean isolated installation can show command help and load packaged resources using only declared package artifacts

### Requirement: Development and release dependency states are reproducible

Repository verification SHALL use the committed lock without silently updating it. Changing a runtime dependency version or compatibility boundary SHALL update the lock and exercise the affected integration before release.

#### Scenario: Locked verification
- **WHEN** continuous integration verifies an unchanged dependency state
- **THEN** it fails on a stale lock rather than resolving and recording a different dependency graph implicitly

#### Scenario: Dependency compatibility changes
- **WHEN** a maintainer changes a runtime compatibility range
- **THEN** the reviewed change includes the corresponding lock update and integration evidence

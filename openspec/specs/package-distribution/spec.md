# Package Distribution Specification

## Purpose

Provide reproducible bundled external resources without maintaining duplicate authoring copies.

## Requirements

### Requirement: External packaged resources have one pinned build source

Externally maintained skills bundled with Powerspec SHALL be declared as an immutable upstream source and selected paths rather than committed as duplicate authoring copies in the Powerspec catalog. Building the source distribution SHALL materialize and validate that declaration, including the selected complete skill roots, upstream license, revision provenance, and deterministic paths. A missing resource, invalid skill root, revision mismatch, path escape, or source acquisition failure SHALL fail the build rather than emit a partial catalog.

The resulting source distribution SHALL carry the resolved snapshot required to build its wheel without network access. Wheels built directly from the reviewed checkout and from that source distribution SHALL expose the same packaged builtin resource set. Installed runtime commands SHALL read those packaged resources without acquiring or refreshing the upstream source.

#### Scenario: Build resolves the declared OpenSpec skills
- **WHEN** a release source distribution is built from a checkout containing the pinned OpenSpec build-source declaration
- **THEN** the artifact contains the selected complete skills, license, and exact revision provenance without requiring tracked duplicate skill directories

#### Scenario: Declared source cannot be reproduced
- **WHEN** the pinned revision or selected skill paths cannot be acquired and validated
- **THEN** the build fails without publishing a partial or differently sourced catalog

#### Scenario: Wheel is rebuilt from the source distribution
- **WHEN** a wheel is built offline from the completed source distribution
- **THEN** it contains the same builtin resource paths and content as the wheel built from the reviewed checkout

#### Scenario: Installed runtime uses the packaged snapshot
- **WHEN** an installed Powerspec command resolves a builtin OpenSpec skill
- **THEN** it reads the packaged snapshot without contacting the upstream repository or requiring a development checkout

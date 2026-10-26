## MODIFIED Requirements

### Requirement: Bundled workflows have an explicit CLI compatibility floor

Powerspec SHALL document and enforce OpenSpec 1.14.3 or later for fresh OpenSpec bootstrap. This floor SHALL be the oldest OpenSpec CLI release compatible with the bundled workflow skills and with Powerspec's own OpenSpec invocations; it MAY be older than the release of the bundled snapshot, which is v1.15.0. The floor SHALL be raised only when a bundled skill or a Powerspec invocation depends on newer CLI behavior, and documentation SHALL state the bundled snapshot release and the floor separately. Doctor SHALL report an older CLI as incompatible. Rejection SHALL precede OpenSpec initialization and SHALL NOT upgrade the CLI or replace existing consumer configuration.

#### Scenario: Older CLI cannot bootstrap
- **WHEN** fresh bootstrap discovers OpenSpec 1.14.2 or an earlier version
- **THEN** it reports the required minimum version without invoking initialization or creating consumer files

#### Scenario: Compatible CLI initializes without local agent tools
- **WHEN** fresh bootstrap discovers OpenSpec 1.14.3 or a newer compatible version
- **THEN** it initializes OpenSpec with native agent-tool generation disabled, preserving Powerspec's skill provisioning boundary

#### Scenario: Floor older than the bundled snapshot
- **WHEN** Powerspec bundles the v1.15.0 workflow skills and fresh bootstrap discovers OpenSpec 1.14.3
- **THEN** bootstrap proceeds and doctor reports the CLI as compatible

#### Scenario: Doctor reports compatibility without mutation
- **WHEN** doctor inspects an older OpenSpec CLI
- **THEN** it reports a failed compatibility check naming 1.14.3 without installing or updating software

# Spec Delta

## ADDED Requirements

### Requirement: Bundled workflows have an explicit CLI compatibility floor

Powerspec SHALL document and enforce OpenSpec 1.14.3 or later for fresh OpenSpec bootstrap alongside its bundled v1.14.3 workflow skills. Doctor SHALL report an older CLI as incompatible. Rejection SHALL precede OpenSpec initialization and SHALL NOT upgrade the CLI or replace existing consumer configuration.

#### Scenario: Older CLI cannot bootstrap
- **WHEN** fresh bootstrap discovers OpenSpec 1.14.2 or an earlier version
- **THEN** it reports the required minimum version without invoking initialization or creating consumer files

#### Scenario: Compatible CLI initializes without local agent tools
- **WHEN** fresh bootstrap discovers OpenSpec 1.14.3 or a newer compatible version
- **THEN** it initializes OpenSpec with native agent-tool generation disabled, preserving Powerspec's skill provisioning boundary

#### Scenario: Doctor reports compatibility without mutation
- **WHEN** doctor inspects an older OpenSpec CLI
- **THEN** it reports a failed compatibility check naming 1.14.3 without installing or updating software

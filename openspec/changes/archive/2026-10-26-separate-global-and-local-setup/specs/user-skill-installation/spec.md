## MODIFIED Requirements

### Requirement: Provisioning is repeatable and reports partial failures

Matching installed resources SHALL be reused. Conflicting unmanaged or locally modified targets SHALL be reported rather than silently overwritten. Repeated initialization SHALL preserve project configuration and unrelated user-level resources. Partial provisioning failures SHALL identify completed and failed actions without claiming rollback or successful completion of the whole bundle. Skill lookup SHALL never perform repair installation implicitly.

An explicit `pspec upgrade --force` or `pspec init --agent <agent> --force`, or an accepted interactive init confirmation, SHALL permit ZuAT to recoverably replace selected unowned or locally modified skill targets after complete inspection. It SHALL NOT bypass incomplete inspection, unsupported targets, source validation, hook ownership checks, or obsolete-skill removal safeguards. Without that authorization, an exact unowned copy MAY be adopted without rewriting its bytes, while a differing unowned or modified copy SHALL remain a conflict. A conflict failure SHALL name the command that authorizes its replacement.

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

#### Scenario: Explicit replacement during forced init
- **WHEN** a selected skill already exists with differing unowned or locally modified content and the user runs `pspec init --agent <agent> --force`
- **THEN** Powerspec asks ZuAT to archive and replace that selected target and reports the resulting action and its recovery operation

#### Scenario: Conflict names its remedy
- **WHEN** a completely inspected selected skill remains an unowned or modified conflict without replacement authorization
- **THEN** its failure diagnostic names `pspec init --agent <agent> --force` as the command that authorizes recoverable replacement

#### Scenario: Incomplete inspection is never forced
- **WHEN** replacement is authorized but a target's inspection is incomplete or unsupported
- **THEN** that target fails with its diagnostics and is not replaced

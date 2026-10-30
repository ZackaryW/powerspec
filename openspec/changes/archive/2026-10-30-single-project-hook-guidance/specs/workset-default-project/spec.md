## ADDED Requirements

### Requirement: Workset default selects the delivered guidance
When a multi-project hook payload's workspace paths exactly match the member snapshot of one stored default, the message SHALL name that default project and deliver only its guidance, marking it as the default in the project list. Without exactly one match there SHALL be no default and no guidance body.

#### Scenario: Session matches a workset with a default
- **WHEN** the payload lists exactly the member paths of `poc-ab` and its default is `poc-ab-central`
- **THEN** the message names `poc-ab-central` as the default and contains its guidance and no other project's guidance

#### Scenario: Default project has no guidance
- **WHEN** the matched default project contributes no guidance
- **THEN** the message still names it as the default, with the project list and command, and no empty section

#### Scenario: Default guidance fails to resolve
- **WHEN** the matched default project's guidance cannot be resolved
- **THEN** stderr names that project, the message is delivered with the project list and command but no guidance, and the exit status is zero

#### Scenario: Session is a subset of a workset
- **WHEN** the payload lists only some of a workset's member paths
- **THEN** no default is named and no guidance body is delivered

#### Scenario: Two stored snapshots match
- **WHEN** two stored worksets have exactly the payload's member paths
- **THEN** no default is named, no guidance body is delivered, and stderr reports the ambiguity

## MODIFIED Requirements

### Requirement: Default lookup in hooks is local and failure-tolerant
Hook dispatch SHALL read defaults only from the Powerspec user file and SHALL NOT invoke OpenSpec or any other process to resolve them. A missing file means no default; an unreadable or malformed file SHALL be reported on stderr while the project list is still delivered without a default.

#### Scenario: No defaults file
- **WHEN** `~/.powerspec/worksets.toml` does not exist
- **THEN** the project list is delivered without a default and without a diagnostic

#### Scenario: Malformed defaults file
- **WHEN** the file is not valid TOML
- **THEN** stderr names the file, the project list is still delivered without a default, and the exit status is zero

## REMOVED Requirements

### Requirement: Multi-project guidance names the workset default
**Reason**: Multi-project sessions no longer combine guidance, so the default is no longer a fallback among sections; it selects the only guidance delivered.
**Migration**: None; existing stored defaults keep working and now select the delivered guidance.

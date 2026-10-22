# Spec Delta

## Purpose

Define the behavioral evidence required by testing skills and selected development governance so verification demonstrates accepted outcomes without manufacturing coverage or confusing text presence with execution.

## ADDED Requirements

### Requirement: Testing skills require a discriminating behavioral claim
The TDD and BDD skills SHALL require an accepted behavior, regression, or externally meaningful contract, its observation boundary, and a plausible violation the selected check would detect. Verification SHALL exercise the relevant production path. Passing assertions SHALL support only the outcomes they actually observe.

#### Scenario: TDD verification identifies missing behavior
- **WHEN** a TDD segment chooses a test for a new behavior or regression
- **THEN** the skill directs the author to identify the expected observable outcome and why the missing or defective behavior makes that check fail
- **AND** existing working behavior is not broken merely to manufacture a red result

#### Scenario: BDD example exercises the accepted outcome
- **WHEN** a BDD example claims an OpenSpec scenario is covered
- **THEN** its triggering action exercises the relevant production interaction and its assertions establish the scenario's observable outcomes
- **AND** a matching scenario title, feature text, or step binding alone is insufficient evidence

### Requirement: Implementation text matching is not behavioral evidence
The testing skills SHALL prohibit tests added solely to match source strings, regex patterns, snapshots, names, or implementation fragments without establishing a required contract. The prohibition SHALL apply regardless of assertion syntax. Renaming an assertion or replacing substring matching with regex, snapshots, or parsed source inspection SHALL NOT make implementation mirroring sufficient.

#### Scenario: Source contains an expected call
- **WHEN** a proposed test searches implementation source for a save call and claims that a command persists data
- **THEN** the skill rejects that evidence and directs verification of the command's persisted result through the appropriate isolated boundary

#### Scenario: Passing check cannot distinguish the defect
- **WHEN** a check would still pass if the claimed behavior were absent while its expected source fragment remained present
- **THEN** the author replaces or strengthens the check to detect the behavior violation instead of retaining it for a passing-test count

### Requirement: Text assertions require an actual text contract
The skills SHALL allow string, regex, and snapshot assertions when observable text or an authored artifact is itself the accepted contract. They SHALL prefer parsed semantic assertions for structured outputs unless representation is contractual, and avoid pinning incidental wording or formatting. Expected outcomes SHALL derive from the accepted contract rather than copying the implementation's computation.

#### Scenario: CLI output or regex behavior is contractual
- **WHEN** a requirement specifies a CLI diagnostic, serialized representation, or pattern-matching result
- **THEN** tests may compare the produced text or matching result at the relevant boundary using examples that distinguish valid and invalid behavior

#### Scenario: Generated configuration has a structural contract
- **WHEN** a command must publish a configuration value but whitespace and key order are not contractual
- **THEN** verification parses the generated configuration and checks the required value rather than freezing incidental rendering

#### Scenario: Generated instructions are delivered
- **WHEN** a test verifies selected guidance appears in resolver output or a published artifact
- **THEN** it may verify the delivered content and relevant selection conditions
- **AND** its evidence is limited to content delivery and does not establish host receipt, agent adherence, or execution of those instructions

### Requirement: Selected governance requires meaningful verification
The Python CLI bundle's task-planning and apply guidance SHALL require verification at the changed boundary with a stated behavior or contract and detectable failure. It SHALL reject manufactured source-text checks and preserve the text-contract exception. These reminders SHALL NOT activate BDD, duplicate entire skill procedures, or claim automatic enforcement of test quality.

#### Scenario: Planning and review consume the governance
- **WHEN** the selected Python CLI context is published for task planning and application
- **THEN** its reminders direct authors and reviewers to connect proposed assertions to observable outcomes and reject implementation-text substitutes
- **AND** existing profile exclusions, skill selection, and publication ownership remain unchanged

### Requirement: Verification remains proportional and honest
The skills and governance SHALL permit reuse of relevant coverage and appropriate non-test validation for changes without behavioral effects. They SHALL NOT require tests merely to increase counts or confirm that a new instruction contains prescribed wording. Evidence SHALL distinguish automated behavior checks, content or artifact validation, manual review, and unverified agent adherence.

#### Scenario: Governance wording changes
- **WHEN** only skill prose or a governance instruction changes and existing delivery coverage remains applicable
- **THEN** semantic review and relevant artifact or delivery validation are acceptable without manufacturing a red-green cycle or a keyword-presence test for the new rule

#### Scenario: Existing meaningful coverage is retained
- **WHEN** directly affected tests include both useful outcome assertions and incidental prose checks
- **THEN** review preserves the behavioral coverage while revising or removing only the unnecessary dependencies on incidental text

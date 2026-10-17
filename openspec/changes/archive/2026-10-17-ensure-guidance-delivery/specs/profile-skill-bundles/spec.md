## ADDED Requirements

### Requirement: Guidance bodies can share one contained file
Context attachments and runtime traits SHALL accept exactly one of inline `body` or `body_file`. A body file SHALL be UTF-8 text at a relative path within the owning catalog root; absolute paths, traversal, escaping links, absent files and invalid text SHALL fail with located diagnostics. Catalog loading SHALL resolve the body before existing reference classification, interpolation and condition processing. This SHALL NOT merge context and trait evaluation timing or execute guidance. Existing inline resources SHALL remain valid.

#### Scenario: One instruction serves two destinations
- **WHEN** a context attachment and trait reference the same body file
- **THEN** both receive the same authored text and existing skill-reference classification applies

#### Scenario: Invalid body source
- **WHEN** both body forms, neither form, or an escaping/missing body file is declared
- **THEN** catalog loading fails with a located diagnostic

### Requirement: Zmem standing policy is selected for persistent and runtime delivery
The global zmem lifecycle profile SHALL select both a context and trait sharing one authoritative guidance body. The body SHALL require memory lookup when task history, provenance or prior decisions matter, followed by current-evidence verification, without requiring the user to name zmem. Excluding the profile SHALL remove both contributions. The rule SHALL preserve existing commit authorization and task-specific skill selection.

#### Scenario: Historical rationale question
- **WHEN** the selected profile's guidance is consumed for a question about when or why a decision changed
- **THEN** the guidance calls for zmem-query-memory without a separate permission question

#### Scenario: Profile excluded
- **WHEN** the consumer excludes the zmem profile
- **THEN** neither persistent nor runtime zmem guidance is selected

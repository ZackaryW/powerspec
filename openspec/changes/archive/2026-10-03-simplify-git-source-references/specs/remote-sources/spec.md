## MODIFIED Requirements

### Requirement: Git source references select declared recipe paths directly

Profile skills SHALL support `<alias>/<path-pattern>` strings for direct Git-path selection. The first segment SHALL resolve to a `[[source]]` declaration in the effective profile graph, and the remaining segments SHALL be the source-relative selector. Powerspec SHALL NOT derive a URL from the alias, create a `sources/` resource folder, silently bind an undeclared alias, or require an `@gitsource` namespace. Parsing, status, and runtime arming SHALL retain the alias and selector without fetching. Materialization SHALL use the declared recipe and retain resolved revision and artifact provenance.

Selectors SHALL be source-relative and contained after canonicalization including symlinks. Direct directories SHALL select one skill root; `*` SHALL match immediate child directories and recursive selection SHALL require `**`. Candidate roots SHALL carry `SKILL.md`; unrelated files and folders SHALL not be installed. Empty initial selections, malformed declarations, duplicate declared names, and escaping paths SHALL produce diagnostics. A valid upgrade replacement may be empty for an established selection. Expansion SHALL be deterministic by source-relative path.

Direct Git-path selection SHALL NOT require `.pspec` or write synthetic catalog files into the acquired checkout. Each selected skill SHALL retain its complete resources, declared installed name, alias, source/revision/path provenance, and declaring profile scope. Legacy `@gitsource/...` strings SHALL be rejected rather than maintained as a second authored syntax.

#### Scenario: Zmem wildcard selects its skills
- **WHEN** a profile declares the zmem recipe and selects `zmem/skills/*`
- **THEN** selection uses that recipe's materialization and yields its declared immediate skills with external provenance and unprefixed names

#### Scenario: Alias has no declaration
- **WHEN** a source-relative reference names an alias absent from the effective profile declarations
- **THEN** resolution reports the missing declaration without guessing a URL or treating the alias as a Saucepan app

#### Scenario: Direct selection
- **WHEN** a reference selects one contained source-relative directory with a valid `SKILL.md`
- **THEN** only that complete skill root participates

#### Scenario: Selector escapes or has no skill matches
- **WHEN** a selector is absolute, escapes after canonicalization, or an initial selection has no skill roots
- **THEN** selection reports the relevant diagnostic without installing unrelated files

#### Scenario: Runtime doctor condition is false
- **WHEN** the lifecycle profile selects external skills but its runtime trait condition is false
- **THEN** skill selection and checkpoint context remain selected while only that trait guidance is omitted

#### Scenario: Legacy namespace is rejected
- **WHEN** a profile supplies an `@gitsource/<alias>/<path-pattern>` skill string
- **THEN** validation reports the unsupported legacy syntax and directs migration to `<alias>/<path-pattern>`

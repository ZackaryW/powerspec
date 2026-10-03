## MODIFIED Requirements

### Requirement: Sync selects only compile-time contexts

Both pspec sync and powerspec sync SHALL use the nearest owning consumer within the enclosing Git boundary, including nested consumers and worktrees, and select contexts contributed by its effective profiles. Profile exclusions and subprofile composition SHALL follow profile-skill-bundles. Runtime traits SHALL NOT be compiled, dispatched, or converted into commands in config.yaml. Sync SHALL reuse existing source materializations without refresh. Sync SHALL acquire selected sources with no current materialization and initialize the store/application when needed. Sync SHALL NOT refresh existing revisions, install or remove skills, register hooks, execute procedures, or flush state. Failed acquisitions or unusable existing materializations SHALL produce diagnostics without deleting or replacing existing data; unavailable or removed sources SHALL NOT cause installed-skill deletion. This preservation SHALL NOT prevent normal reconciliation of obsolete managed context guidance. Missing consumers or missing/malformed target configuration SHALL produce diagnostics rather than guessed initialization.

#### Scenario: Python and utility contexts are selected
- **WHEN** a consumer selects the reviewed Python CLI profile containing the utility-planning subprofile
- **THEN** sync publishes the selected Python CLI and utility context attachments at their declared destinations without executing planning or TDD

#### Scenario: Runtime trait also selected
- **WHEN** the effective profile also selects a guarded runtime trait
- **THEN** sync leaves its body and runtime condition out of the generated configuration

#### Scenario: Nearest target is invalid
- **WHEN** the nearest consumer or its existing config.yaml is missing or malformed
- **THEN** sync reports the problem without selecting another consumer or creating guessed configuration

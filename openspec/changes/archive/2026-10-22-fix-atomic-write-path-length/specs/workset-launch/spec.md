# Spec Delta

## MODIFIED Requirements

### Requirement: Transfer retries distinguish completed moves from missing changes

Transfer SHALL retain local, uncommitted progress evidence identifying the selected source, mapped destination, snapshot, transfer mode, and completed stages. Retries SHALL validate that evidence against the requested launch and observed state. A missing source alone SHALL NOT establish a completed move. A matching completed transfer with a resolvable destination SHALL be recognized without overwriting later implementation edits. Partial cleanup SHALL resume only for remaining source entries that still match the verified snapshot and after destination content is verified; unexpected content SHALL remain untouched. For long receipt filenames whose destination paths and short sibling temporary files are supported by the host, transfer SHALL retain and update progress evidence without requiring shorter repository locations or changes to operating-system path policy. Existing receipt identities and locations SHALL remain compatible across this correction.

#### Scenario: Repeat after completed move
- **WHEN** the source change is absent, a matching completion receipt exists, and implementation has updated the destination
- **THEN** launch reports the transfer already completed and preserves the implementation edits

#### Scenario: Missing source without evidence
- **WHEN** no source change is found and no matching completed transfer evidence exists
- **THEN** launch reports the missing change instead of inferring success from a similarly named destination

#### Scenario: Resume interrupted cleanup
- **WHEN** progress records verified transfer but only some source files were removed
- **THEN** a retry verifies the destination and remaining original files before resuming cleanup, preserving any new or changed source files

#### Scenario: Receipt destination approaches the host path limit
- **WHEN** an otherwise valid launch needs a long receipt filename near the host path limit and the host supports both that destination and short temporary files in its parent directory
- **THEN** transfer records its progress and completes normally without relocating repositories or enabling a different operating-system path policy
- **AND** a repeated launch recognizes its receipt at the same location and preserves later destination edits

#### Scenario: Receipt publication fails before transfer
- **WHEN** a launch has prepared worktrees but cannot publish its initial transfer progress evidence
- **THEN** it reports the transfer failure, preserves the selected source and completed worktrees, and does not publish an incomplete output workset
- **AND** after the publication problem is corrected, a retry reuses matching worktrees and completes the requested transfer

# Spec Delta

## Purpose

Keep active OpenSpec planning local while supporting verified incremental commits and zmem authoring, with observable Git-index eligibility checks.

## ADDED Requirements

### Requirement: Commit checks inspect the whole index
`pspec check commit` and `powerspec check commit` SHALL inspect the entire selected Git index, including unchanged tracked paths, without requiring consumer configuration. They SHALL reject active OpenSpec entries and unmerged entries, permit canonical archive contents, and return nonzero when inspection fails. They SHALL honor Git's selected index, including GIT_INDEX_FILE, and support unborn branches, nested invocation directories and linked worktrees.

#### Scenario: New active artifact is staged
- **WHEN** an active change file is staged, including through forced addition despite ignore rules
- **THEN** the check exits 1 and identifies its repository-relative path

#### Scenario: An active artifact was committed previously
- **WHEN** the index retains an unchanged active change artifact and only application code is newly staged
- **THEN** the check still rejects the active artifact

#### Scenario: Implementation checkpoint leaves planning local
- **WHEN** active artifacts exist only as untracked or ignored working files and code or tests are staged
- **THEN** the check succeeds without requiring those active changes to be archived

#### Scenario: Archive replaces active artifacts
- **WHEN** the index removes all active artifacts and contains their canonical archived paths
- **THEN** the check succeeds even when an old commit contained active artifacts

#### Scenario: Alternative index or linked worktree
- **WHEN** the command runs from a nested directory in a linked worktree or with GIT_INDEX_FILE selecting an alternative index
- **THEN** it checks that selected index across the entire repository rather than the main checkout or only the invocation directory

#### Scenario: Invalid or conflicted repository
- **WHEN** Git is unavailable, the invocation is outside a working repository, the index cannot be read, or index entries are unmerged
- **THEN** the check exits 1 without claiming eligibility

### Requirement: Archive eligibility uses path boundaries
The check SHALL recognize an openspec/changes segment pair anywhere in a repository-relative index path, case-insensitively. Only entries beneath its exact lowercase archive directory SHALL qualify for the archive exception. Other entries at or below that boundary SHALL fail, including intent-to-add entries. The check SHALL use Git paths rather than resolving working-tree symlinks or treating substrings as path boundaries.

#### Scenario: Nested consumer and misleading archive name
- **WHEN** nested consumers have entries in openspec/changes/active or openspec/changes/archive-draft
- **THEN** both are rejected while openspec/changes/archive/dated-change content is allowed

#### Scenario: Similar unrelated paths
- **WHEN** entries are in docs/openspec-notes/changes or openspec/specs
- **THEN** the active-change rule does not reject them

#### Scenario: Case variant and unusual filename
- **WHEN** active entries use case variants of OpenSpec/Changes or names containing whitespace, tabs or non-ASCII characters
- **THEN** they remain identifiable as individual forbidden paths without line-based parsing ambiguity

### Requirement: Checks preserve state and report limited evidence
Commit checks SHALL leave working files, index bytes, refs and Git configuration unchanged and SHALL NOT stage, unstage, archive, synchronize, commit, install hooks or invoke zmem. Human failures SHALL use stderr; --json SHALL emit one object with ok, repository, forbidden_paths, unmerged_paths and errors. Exit 0 SHALL establish only index path eligibility, not archive completion, spec synchronization, message validity or a later commit's unchanged index.

#### Scenario: Rejected check preserves unrelated staging
- **WHEN** an active artifact and unrelated changes are staged
- **THEN** the failed check preserves the complete index and working files

#### Scenario: Machine-readable result
- **WHEN** either console alias runs the check with --json
- **THEN** stdout is one parseable result with the identified violations or inspection errors and no progress decoration

### Requirement: Governance preserves incremental code checkpoints
Selected checkpoint guidance SHALL permit coherent verified implementation commits while active planning remains local. It SHALL require inspecting the full proposed index with pspec check commit immediately before every authorized commit and resolving failures without deleting local planning or automatically untracking user files. Guidance SHALL prohibit bypassing a failed check or claiming an earlier check covers a subsequently changed index.

#### Scenario: Active planning remains unfinished
- **WHEN** a verified implementation slice is ready but the overall change remains active
- **THEN** guidance permits the code/test checkpoint and excludes active artifacts without prematurely archiving them

### Requirement: Artifact commits follow sync and archive
Selected standing and archive guidance SHALL require successful delta-spec synchronization and successful archive before staging change artifacts from their archived location. Failed or incomplete synchronization or archive SHALL prevent that artifact commit. Already tracked active files SHALL be explicitly reconciled with their local content preserved; ignoring them alone SHALL NOT be presented as removing them from future commit trees.

#### Scenario: Final artifact commit
- **WHEN** implementation is complete and artifact synchronization and archive succeed
- **THEN** guidance permits the reviewed main-spec and archive changes to be committed after the index check

#### Scenario: Archive or sync fails
- **WHEN** either operation fails or remains incomplete
- **THEN** guidance requires reporting the blocker and withholding the affected artifact commit, without treating a renamed directory as evidence of successful synchronization

### Requirement: Every commit follows zmem authoring
The selected standing policy SHALL call for native zmem-author-commits on every authorized commit, including code, tests, documentation, configuration and archive commits. It SHALL preserve the skill's runtime checks, validation and unavailable-tool reporting, require no manufactured annotation, and grant no new commit or push authorization. Persistent publication and startup/compaction delivery SHALL share this policy.

#### Scenario: Documentation or archive checkpoint
- **WHEN** an authorized checkpoint changes only documentation or archived artifacts
- **THEN** the standing policy still directs use of zmem-author-commits

#### Scenario: Guidance is delivered
- **WHEN** the selected policy is published or returned at startup or compaction
- **THEN** evidence establishes delivery only, not execution of zmem, the index check or compliance by the agent

# Consumer Configuration Specification

## Purpose

Locate the owning project consumer and expose persistent and temporary variable layers without crossing repository or change boundaries.

## Requirements

### Requirement: Consumer discovery respects the invoking Git boundary

Resolution SHALL find the nearest owning openspec/.pspec/config.toml from the invocation directory while stopping at its enclosing Git root, including Git worktree .git files. Invocations within an OpenSpec subtree SHALL use its owning consumer. It SHALL NOT search sibling repositories, parent repositories beyond that boundary, skill installation homes, or authoring checkouts. Malformed nearest configuration SHALL fail rather than falling through. No consumer SHALL yield absent project layers for the caller to combine with applicable defaults; it SHALL NOT create a guessed consumer.

#### Scenario: Nested consumer wins
- **WHEN** both a nearer consumer and a Git-root consumer exist
- **THEN** the nearer consumer supplies project layers

#### Scenario: OpenSpec subtree invocation
- **WHEN** the invocation directory is inside a consumer's OpenSpec subtree
- **THEN** its owning consumer is selected

#### Scenario: Worktree boundary
- **WHEN** the enclosing Git root has a .git file
- **THEN** discovery stops at that root and does not borrow its parent repository

#### Scenario: Malformed nearest consumer
- **WHEN** the nearest consumer file is malformed
- **THEN** resolution reports it instead of choosing another consumer

#### Scenario: No configured consumer
- **WHEN** no applicable consumer exists within the Git boundary
- **THEN** project layers are absent and no files are created

### Requirement: Persistent and temporary variables share a scoped structure

Both config.toml and current.toml SHALL support shared [vars] and direct [_change.<name>] variable keys. Config SHALL be persistent and intended for version control; current SHALL be temporary and intended to be gitignored by initialization. Runtime values SHALL follow current change, current shared, config change, config shared, selected-profile defaults, global-profile defaults, then caller-supplied skill defaults. Change layers SHALL apply only to an explicit change selector; a missing matching table supplies no overrides. A malformed present file SHALL be diagnosed. Layer resolution SHALL retain provenance and SHALL NOT write files, prompt, infer an active change, or perform cleanup. Compile-time context resolution SHALL use persistent shared configuration and profile/declaration defaults only.

#### Scenario: Temporary shared overrides persistent change
- **WHEN** current shared vars and the selected config change table both supply a value and no current change override exists
- **THEN** the current shared value is effective with its provenance

#### Scenario: No temporary file
- **WHEN** current.toml does not exist
- **THEN** persistent and default layers remain available without creating current.toml

#### Scenario: No change inferred
- **WHEN** multiple change tables exist but no change selector is provided
- **THEN** only shared and default layers participate

### Requirement: Change-scoped runtime values preserve independent work

The --change selector SHALL identify the change whose direct [_change.<name>] keys participate in runtime resolution in both consumer files. Lookup SHALL NOT merge another change's variables. Resolved input layers SHALL retain change identity and provenance for callers to produce correctly scoped answer instructions. Lookup SHALL remain read-only. Compile-time configuration SHALL continue to exclude current.toml; this runtime extension SHALL NOT implicitly compile per-change values into shared config.yaml.

#### Scenario: Temporary change value overrides shared values
- **WHEN** current.toml supplies test_command in both [vars] and [_change.fix-cli-output] and lookup passes --change fix-cli-output
- **THEN** the change-specific temporary command is selected

#### Scenario: Persistent change value supplies an override
- **WHEN** config.toml supplies both shared and matching change-specific values and no temporary layer supplies the key
- **THEN** the persistent change value wins over persistent shared values

#### Scenario: Temporary shared value overrides persistent change value
- **WHEN** current.toml [vars] and config.toml's selected change table both supply a key, with no temporary change override
- **THEN** the temporary shared value wins under the temporary-over-persistent precedence

#### Scenario: No change supplied
- **WHEN** lookup has no --change argument and both files contain change-specific tables
- **THEN** only shared values and defaults participate, without selecting any change implicitly

#### Scenario: Different change supplied
- **WHEN** lookup selects a change with no matching tables
- **THEN** shared values and defaults apply without borrowing another change's overrides

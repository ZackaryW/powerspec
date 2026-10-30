# workset-default-project Specification

## Purpose
Let a user declare one member of an OpenSpec workset as its default project, so agents in multi-project sessions have a deterministic fallback when they cannot tell which project a request or OpenSpec action belongs to.

## Requirements

### Requirement: Show, set, and clear a workset default
`pspec workset default <workset> <label>` SHALL set the default member, `pspec workset default <workset>` SHALL show it, and `--clear` SHALL remove it. Each SHALL support `--json` with one stdout object. Setting the current value again SHALL report it unchanged; clearing an absent default SHALL succeed and report nothing removed.

#### Scenario: Set a default
- **WHEN** a user runs `pspec workset default poc-ab poc-ab-central` and both exist
- **THEN** the command reports the default as set and a later show reports `poc-ab-central` with its path

#### Scenario: Repeat the same setting
- **WHEN** the same default is set again
- **THEN** the command reports it unchanged and the stored file is not rewritten

#### Scenario: Clear a default
- **WHEN** a user runs `pspec workset default poc-ab --clear`
- **THEN** the default is removed and a later show reports no default

### Requirement: Setting a default is validated through OpenSpec
Setting SHALL read the saved worksets through OpenSpec and require the named workset to exist and the label to be one of its members. Otherwise it SHALL exit nonzero with a diagnostic and write nothing. Powerspec SHALL NOT create, modify, or reorder the OpenSpec workset.

#### Scenario: Unknown workset
- **WHEN** the named workset is not saved in OpenSpec
- **THEN** the command fails naming the workset and the stored file is unchanged

#### Scenario: Label is not a member
- **WHEN** the label is not a member of the workset
- **THEN** the command fails listing the workset's member labels and writes nothing

#### Scenario: OpenSpec workset is untouched
- **WHEN** a default is set or cleared
- **THEN** `openspec workset list` reports the same members, order, and tool as before

### Requirement: Defaults are stored in a Powerspec-owned user file
Defaults SHALL be stored in `~/.powerspec/worksets.toml`, keyed by workset name, each entry holding the default label, its resolved path, and the resolved paths of every member at the time it was recorded. Writes SHALL be atomic and SHALL preserve other worksets' entries.

#### Scenario: Two worksets keep separate defaults
- **WHEN** defaults are set for two worksets
- **THEN** both entries exist and changing one leaves the other byte-identical in meaning

#### Scenario: Interrupted write
- **WHEN** a write fails partway
- **THEN** the previous file content remains readable and unchanged

### Requirement: Stale defaults are reported, never guessed
Showing a default SHALL report it stale, with the reason, when the workset no longer exists in OpenSpec, the label is no longer a member, or the stored member paths differ from OpenSpec's current members. A stale default SHALL NOT be re-pointed automatically.

#### Scenario: Workset removed
- **WHEN** the OpenSpec workset was removed after its default was set
- **THEN** show reports the default stale because the workset no longer exists

#### Scenario: Membership changed outside Powerspec
- **WHEN** a member was added through OpenSpec directly
- **THEN** show reports the default stale because the member snapshot differs, and suggests setting it again

### Requirement: Default lookup in hooks is local and failure-tolerant
Hook dispatch SHALL read defaults only from the Powerspec user file and SHALL NOT invoke OpenSpec or any other process to resolve them. A missing file means no default; an unreadable or malformed file SHALL be reported on stderr while the project list is still delivered without a default.

#### Scenario: No defaults file
- **WHEN** `~/.powerspec/worksets.toml` does not exist
- **THEN** the project list is delivered without a default and without a diagnostic

#### Scenario: Malformed defaults file
- **WHEN** the file is not valid TOML
- **THEN** stderr names the file, the project list is still delivered without a default, and the exit status is zero

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

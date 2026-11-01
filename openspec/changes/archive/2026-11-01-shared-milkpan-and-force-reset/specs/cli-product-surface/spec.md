# Spec Delta

## MODIFIED Requirements

### Requirement: Status and doctor inspect without mutation

`pspec status` SHALL describe the owning consumer, selected profile or global-only mode, effective profiles after exclusions, selected contexts, traits, skills, sources and pending installation facts without acquiring or modifying resources. `pspec doctor` SHALL check the consumer boundary and required executables and integrations without repairing them, unless `--force-reset` is given. Both SHALL support human and `--json` output, and status SHALL report installation-selected skills separately from resolve-skills declarations.

#### Scenario: Inspect a configured consumer
- **WHEN** a user runs status inside a valid consumer
- **THEN** Powerspec reports the effective configuration and unresolved availability facts without changing files or installations

#### Scenario: Diagnose missing prerequisites
- **WHEN** doctor finds a missing or incompatible prerequisite
- **THEN** it reports a failed named check, exits nonzero, and makes no repair attempt

#### Scenario: Inspect resolve-only availability
- **WHEN** a consumer selects a skill only through resolve-skills
- **THEN** status reports its resolution selection separately from installation selections without materializing sources or inspecting native copies

#### Scenario: Status JSON keeps the skills field meaning
- **WHEN** status reports a skill that is both selected for installation and declared in resolve-skills
- **THEN** the skills field keeps installation semantics, the additive resolve_skills field also lists it, and human output labels the two lists separately without implying installation success

### Requirement: Doctor distinguishes milkpan compatibility from source readiness

Doctor SHALL label its successful milkpan observation as an executable compatibility check (protocol and version), without implying initialized selections. For the managed route it SHALL separately report whether the shared `milkpan` link exists and whether its release line is supported; an explicit override SHALL be labelled standalone. Results SHALL state these limitations without mutation.

#### Scenario: Compatible binary but no selected source
- **WHEN** doctor observes a compatible milkpan executable
- **THEN** its detail identifies executable compatibility, reports the managed link state separately when applicable, and states that selected-source readiness was not checked

#### Scenario: Managed link behind the pin
- **WHEN** the shared link holds a milkpan outside the supported release lines
- **THEN** doctor reports that the next preparation or upgrade will switch it, without modifying anything

#### Scenario: Explicit standalone override
- **WHEN** the user selects an external milkpan through POWERSPEC_MILKPAN
- **THEN** doctor labels that selection standalone without checking managed state or changing the binary

## REMOVED Requirements

### Requirement: First-use preparation bootstraps Powerspec's own milkpan
**Reason**: Powerspec no longer has its own milkpan home.
**Migration**: See "First-use preparation uses the shared milkpan".

## ADDED Requirements

### Requirement: First-use preparation uses the shared milkpan

Source preparation SHALL use the shared milkpan bucket, bootstrapping the pinned, verified release only when no supported milkpan is linked there. It SHALL NOT adopt, migrate or modify a Saucepan installation or store, replace credentials, bypass guards or substitute test keys.

#### Scenario: Fresh machine
- **WHEN** no shared milkpan bucket exists
- **THEN** preparation bootstraps and links the pinned milkpan in `~/.milkpan` before acquiring the selected sources

#### Scenario: Old Saucepan store present
- **WHEN** a Saucepan store and `saucepan-state.json` from an earlier Powerspec exist
- **THEN** preparation leaves them untouched and creates fresh milkpan selections

#### Scenario: Canonical GitHub source identity
- **WHEN** a recipe names an HTTPS GitHub repository with different owner/repository letter case or a `.git` suffix
- **THEN** it maps to the same canonical milkpan GitHub spec, while other parts of the reference stay distinct

#### Scenario: Credential or store failure stays an error
- **WHEN** milkpan reports a failure for the bucket or for GitHub credentials
- **THEN** source preparation reports an error and claims no success

#### Scenario: Upgrade does not replace missing initialization
- **WHEN** a consumer's sources were never initialized
- **THEN** upgrade does not silently perform that missing initialization

### Requirement: Doctor force reset clears all local state

`pspec doctor --force-reset` SHALL delete the whole shared milkpan bucket (including content other tools stored there), all of `~/.powerspec`, and the current project's `milkpan-state.json` and its lock, after listing them and receiving confirmation (`--yes` or an interactive answer). It SHALL report each removed and remaining path, exit nonzero when anything remains, and run no other checks.

#### Scenario: Confirmed reset
- **WHEN** a user runs `pspec doctor --force-reset --yes`
- **THEN** the bucket, `~/.powerspec` and the project's selection state are removed, and the next `pspec init` bootstraps from scratch

#### Scenario: No confirmation available
- **WHEN** `--force-reset` runs non-interactively without `--yes`
- **THEN** it lists what would be deleted, deletes nothing and exits nonzero

#### Scenario: Files in use
- **WHEN** a milkpan process is still running from the bucket on Windows
- **THEN** reset removes everything else, lists the paths it could not delete and exits nonzero

### Requirement: Force reset refuses unrecognized bucket locations

Before deleting the bucket, reset SHALL require the resolved bucket path to be absent, empty, or recognizably a milkpan bucket (holding milkpan's state, blobs or policy file), and SHALL refuse a filesystem root or the user's home directory itself.

#### Scenario: MILKPAN_HOME points at a project folder
- **WHEN** `MILKPAN_HOME` names a directory with unrelated files and no milkpan state
- **THEN** reset refuses to delete it, names the path and deletes nothing else

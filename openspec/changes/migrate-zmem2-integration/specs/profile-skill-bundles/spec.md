# Spec Delta

## ADDED Requirements

### Requirement: Memory skills use the zmem2 source with stable identities
The bundled global zmem lifecycle profile SHALL acquire its memory skills from `https://github.com/ZackaryW/zmem2` at `main` through Saucepan. It SHALL preserve the `zmem` source alias, `zmem/skills/*` selector, `@builtin/zmem-lifecycle` profile identity and user scope. Source migration SHALL retain existing selection and native ownership safeguards.

#### Scenario: Fresh memory profile selection
- **WHEN** a consumer initializes with the bundled memory profile selected
- **THEN** its memory skills come from zmem2 and retain the names zmem-query-memory, zmem-author-commits and zmem-design-extensions

#### Scenario: Consumer retains a predecessor selection
- **WHEN** the bundled source origin changes and the consumer has only a retained predecessor recipe
- **THEN** initialization prepares a distinct zmem2 selection without treating the predecessor selection as the new source or deleting its retained output
- **AND** provisioning reuses matching installed skills, updates unmodified owned skills and preserves conflicting native edits under the existing ownership contract

#### Scenario: Memory profile excluded
- **WHEN** the consumer excludes @builtin/zmem-lifecycle
- **THEN** that profile contributes no memory skills or memory guidance and its source is not acquired merely because it is bundled

### Requirement: Memory guidance identifies the intended runtime
The shared memory standing guidance SHALL identify zmem2's TypeScript/Node CLI as the intended runtime and require executable-location and command-surface verification when selecting it. It SHALL distinguish skill provisioning from runtime installation, preserve explicit installation authorization, and remain visible when the runtime is absent or incompatible.

#### Scenario: Legacy command shadows the intended runtime
- **WHEN** the selected zmem executable exposes the predecessor command surface
- **THEN** guidance directs the agent to report the mismatch and use an explicitly available compatible executable, without claiming a completed memory check or silently replacing the runtime

#### Scenario: Skills installed without the executable
- **WHEN** Powerspec provisions the zmem2 skills but no compatible runtime is installed
- **THEN** initialization does not imply runtime readiness or install a runtime automatically, and memory guidance retains its unavailable-tool fallback

#### Scenario: Existing lifecycle delivery
- **WHEN** persistent context or an eligible startup or compaction hook delivers memory guidance
- **THEN** both use the same intended-runtime instruction without a successful service probe as a prerequisite

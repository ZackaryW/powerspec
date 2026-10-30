# Spec Delta

## MODIFIED Requirements

### Requirement: Hook dispatch resolves the invoking consumer

Hook dispatch SHALL use the hook process's working directory, also the condition cwd, and its nearest owning consumer within the Git boundary, including worktrees, except that an invocation explicitly requesting payload workspace discovery SHALL use the workspace directories it obtains in place of the working directory, each resolving its own nearest consumer. Stdin SHALL NOT otherwise supply consumer location, and SHALL NOT supply event identity, variable values or user answers. It SHALL select matching runtime traits from the consumer's effective profiles and return agent-supported guidance. An absent consumer or no matching trait SHALL yield no guidance; malformed nearest configuration SHALL be diagnosed.

#### Scenario: Shared dispatcher serves different projects
- **WHEN** the same user-level dispatcher is invoked from two consumers with different effective hook traits
- **THEN** each receives guidance selected from its own process working directory and configuration without reinstalling hooks

#### Scenario: Shared dispatcher serves different projects from a fixed host directory
- **WHEN** the same user-level Antigravity dispatcher runs from one fixed host directory for two sessions whose payloads name different consumers
- **THEN** each receives guidance selected from its own payload workspaces and configuration without reinstalling hooks

#### Scenario: Malformed configuration in a multi-project session
- **WHEN** a payload lists several workspaces and one consumer's nearest configuration is malformed
- **THEN** that consumer's failure is reported without selecting a more distant consumer for it, and only that consumer's guidance is withheld

#### Scenario: Global bootstrap profile is excluded
- **WHEN** the invoking consumer excludes the global profile
- **THEN** the shared hook registration remains installed and delivers only the other eligible traits, with no universal bootstrap reminder

#### Scenario: Environment-only session
- **WHEN** a supported lifecycle callback fires during environment maintenance
- **THEN** any applicable skill reminder preserves its task conditions without activating TDD, BDD, or their input questions

#### Scenario: Agent receives a decision request
- **WHEN** an eligible trait's guidance asks the agent to obtain a user decision
- **THEN** the request appears in returned additional context and the hook exits without prompting, reading an answer, or changing variables

#### Scenario: Nested directory in a worktree
- **WHEN** the command runs from a nested directory in a Git worktree
- **THEN** it resolves the nearest consumer within that worktree's Git boundary and evaluates conditions with the actual invocation cwd

#### Scenario: Nearest configuration is malformed
- **WHEN** the nearest consumer configuration is malformed
- **THEN** dispatch reports that configuration failure without selecting a more distant consumer or returning successful partial guidance

#### Scenario: Mixed and repeated runtime mentions
- **WHEN** an eligible message mentions dynamic skill A twice and ordinary skill B
- **THEN** its heading lists A once and its body preserves B's ordinary native invocation without adding B to the dynamic list

#### Scenario: Deferred remote resource is available
- **WHEN** an eligible message references a selected remote skill whose existing materialization contains a valid manifest
- **THEN** dispatch identifies it as dynamic using read-only metadata inspection and does not acquire or refresh the source

#### Scenario: Deferred wildcard reference
- **WHEN** an eligible message names a skill selected through a remote wildcard and the materialization is available
- **THEN** dispatch verifies the declared name against the selected resources before classifying its manifest
- **AND** a missing name is not assumed to exist solely because a wildcard was selected

#### Scenario: Remote metadata is unavailable
- **WHEN** a referenced remote skill's metadata cannot be inspected because the source service, executable, or materialization is unavailable
- **THEN** the message explicitly identifies that skill's classification as unknown and directs inspection through native skill selection
- **AND** independent eligible guidance remains available without installing or repairing anything

#### Scenario: Metadata budget is exhausted
- **WHEN** read-only remote metadata inspection reaches its finite budget
- **THEN** unresolved names receive the unknown fallback without retries or an increase to the native handler timeout

#### Scenario: Invalid readable metadata
- **WHEN** a referenced skill's readable manifest is malformed or selected resources give conflicting known classifications for its name
- **THEN** dispatch reports an authored-resource error without silently treating the skill as ordinary or returning successful partial guidance

#### Scenario: Inactive trait has a remote mention
- **WHEN** a trait is excluded by event selection or its condition is false
- **THEN** its skill references cause no metadata lookup and no heading

#### Scenario: Source becomes available later
- **WHEN** a later supported callback can inspect metadata that was previously unavailable
- **THEN** that callback classifies the reference from current evidence rather than reusing the prior unknown result

### Requirement: Provision generic user-level hook dispatchers through ZuAT

Provisioning SHALL install generic `pspec resolve hook` registrations on the selected agent's supported user-level hook surfaces through ZuAT, each advisory handler having an explicit timeout of at most five seconds and, where the host's handler format has a status field, a concise status. Registrations SHALL carry the native context to select guidance at invocation, not one consumer's profile or trait body, and SHALL NOT return a blocking host decision.

#### Scenario: Repeated dispatcher provisioning
- **WHEN** the selected agent already has matching bounded Powerspec registrations alongside unrelated hooks
- **THEN** provisioning preserves unrelated entries and does not duplicate Powerspec callbacks

#### Scenario: Safely owned earlier callback shape
- **WHEN** ZuAT identifies an unmodified Powerspec-owned registration using a legacy command or resume matcher
- **THEN** provisioning replaces it with the current bounded registration and leaves unrelated providers untouched

#### Scenario: Consumer changes its selected hook traits
- **WHEN** a consumer changes profile selection after user-level hooks have been installed
- **THEN** subsequent matching lifecycle callbacks resolve that consumer's new effective hook traits without rewriting shared registrations

#### Scenario: Exact unowned registration
- **WHEN** complete inspection identifies a unique unowned group exactly matching the desired hooks
- **THEN** provisioning adopts ownership without modifying native bytes or duplicating callbacks

#### Scenario: Unresolved group identity
- **WHEN** inspection is incomplete, ambiguous, or indeterminate, including unowned legacy hooks that cannot be uniquely identified
- **THEN** provisioning reports failure and preserves native settings without attempting installation

#### Scenario: Receipt repair is explicit
- **WHEN** the installed group matches the desired source but its valid owned receipt is stale
- **THEN** ordinary provisioning fails with explicit repair guidance
- **AND** authorized repair reconciles ownership without changing native bytes or modification time and reports a recovery operation identifier

#### Scenario: Repair does not authorize unrelated replacement
- **WHEN** hook repair is authorized but the installed content differs from the desired source or selection is ambiguous
- **THEN** provisioning fails without rewriting settings or replacing an occupant by its array position

#### Scenario: Native hooks change after consumer inspection
- **WHEN** another writer restores the older owned hooks after Powerspec inspects a source-matching receipt conflict but before repair runs
- **THEN** the provider rechecks receipt-only eligibility inside the update operation and rejects repair without replacing the concurrent content

#### Scenario: Unsupported hook surface
- **WHEN** the selected agent has no supported user-level hook surface for a logical event
- **THEN** provisioning reports it without guessing a native event or falling back to repository-local hooks

#### Scenario: Host handler has no status field
- **WHEN** provisioning generates the Antigravity registration, whose handler format has no status message
- **THEN** the handler carries only the host-documented fields and its bounded timeout, with no invented status

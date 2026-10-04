# Spec Delta

## MODIFIED Requirements

### Requirement: Hook dispatch resolves the invoking consumer

Hook dispatch SHALL use the hook command's process working directory and the nearest owning OpenSpec consumer within its enclosing Git boundary, including worktrees. That invocation directory SHALL also supply the cwd used for runtime condition evaluation. Standard input SHALL NOT supply consumer location, event identity, variable values, or user answers. It SHALL select matching runtime traits from that consumer's effective profiles and return guidance in a form supported by the invoking agent. Dispatcher plumbing SHALL NOT publish context attachments, resolve unrelated skill inputs, prompt for skill choices, execute skills, or mutate project/installation state. If returned guidance calls for a user decision, that request SHALL be delivered to the agent as stdout context; the hook command SHALL NOT collect an answer or wait for one. Trusted condition calls SHALL follow the separate capability contract without a claim of isolation or rollback. An absent consumer or no matching active trait SHALL yield no guidance. Malformed nearest configuration SHALL be diagnosed rather than falling through to another consumer.

#### Scenario: Shared dispatcher serves different projects
- **WHEN** the same user-level dispatcher is invoked from two consumers with different effective hook traits
- **THEN** each receives guidance selected from its own process working directory and configuration without reinstalling hooks

#### Scenario: Global bootstrap profile is excluded
- **WHEN** the invoking consumer excludes the global profile and no other active trait supplies bootstrap guidance
- **THEN** the shared hook registration remains installed but emits no bootstrap guidance for that consumer

#### Scenario: Environment-only session
- **WHEN** a matching bootstrap hook fires during environment maintenance
- **THEN** it supplies the bootstrap instruction without activating TDD, BDD, or their input questions

#### Scenario: Agent receives a decision request
- **WHEN** an eligible trait's guidance asks the agent to obtain a user decision
- **THEN** the request appears in returned additional context and the hook exits without prompting, reading an answer, or changing variables

#### Scenario: Nested directory in a worktree
- **WHEN** the command runs from a nested directory in a Git worktree
- **THEN** it resolves the nearest consumer within that worktree's Git boundary and evaluates conditions with the actual invocation cwd

#### Scenario: Nearest configuration is malformed
- **WHEN** the nearest consumer configuration is malformed
- **THEN** dispatch reports that configuration failure without selecting a more distant consumer or returning successful partial guidance

## ADDED Requirements

### Requirement: Native matchers own event source filtering

Installed native registration matchers SHALL select which supported lifecycle callbacks invoke Powerspec. The command's event and agent arguments SHALL select the corresponding supported mapping without inspecting stdin to revalidate native event names or source fields. Direct invocation of a supported logical event SHALL resolve its guidance without claiming that a native lifecycle event occurred. Existing startup, clear, supported fork, and compaction mappings, forbidden high-frequency registrations, five-second native handler timeouts, and per-trait exclusions SHALL remain in force.

#### Scenario: Resume does not start Powerspec
- **WHEN** the native host emits SessionStart with source resume
- **THEN** no installed Powerspec matcher selects it and no Powerspec condition or doctor runs for that event

#### Scenario: Compaction maps through arguments
- **WHEN** the compact matcher invokes `pspec resolve hook afterCompaction --agent codex`
- **THEN** Powerspec selects afterCompaction guidance and emits the supported SessionStart additional-context response without inspecting a native source field

#### Scenario: Direct inspection of guidance
- **WHEN** a caller explicitly runs `pspec resolve hook sessionStart --agent claude` in a configured consumer
- **THEN** the command returns applicable guidance without requiring proof of a native SessionStart event and without claiming the agent followed it

# Trait Hook Delivery Specification

## Purpose

Deliver trait-owned guidance through portable logical hook selection and verified native callbacks using each event's current consumer configuration.

## Requirements

### Requirement: Bootstrap discovery uses runtime trait guidance

The global builtin profile SHALL reference a runtime trait directing the agent to pspec-skill-bootstrap as well as the skill itself. Hook selectors and guidance SHALL belong to the trait. The bootstrap trait SHALL select the Powerspec logical events sessionStart and afterCompaction to introduce its instruction at session start and restore it after compaction. These events SHALL deliver the bootstrap reminder without automatically executing other skills. Supported native hooks SHALL invoke `pspec hook <event>` to obtain applicable guidance. Documentation and validation SHALL distinguish installation, hook invocation, context delivery, agent adherence, and skill execution. Installing, dispatching, or resolving guidance SHALL NOT claim that its workflow ran.

#### Scenario: Installed but unused
- **WHEN** the bundle's skills have been installed but the session never invokes them
- **THEN** no testing workflow is activated and installation reports only availability

### Requirement: Hook dispatch resolves the invoking consumer

Hook dispatch SHALL use the event's working directory and the nearest owning OpenSpec consumer within its enclosing Git boundary, including worktrees. It SHALL select matching runtime traits from that consumer's effective profiles and return guidance in a form supported by the invoking agent. Dispatcher plumbing SHALL NOT publish context attachments, resolve unrelated skill inputs, prompt for skill choices, execute skills, or mutate project/installation state. Trusted condition calls SHALL follow the separate capability contract without a claim of isolation or rollback. An absent consumer or no matching active trait SHALL yield no guidance. Malformed nearest configuration SHALL be diagnosed rather than falling through to another consumer.

#### Scenario: Shared dispatcher serves different projects
- **WHEN** the same user-level dispatcher is invoked from two consumers with different effective hook traits
- **THEN** each receives guidance selected from its own configuration without reinstalling hooks

#### Scenario: Global bootstrap profile is excluded
- **WHEN** the invoking consumer excludes the global profile and no other active trait supplies bootstrap guidance
- **THEN** the shared hook registration remains installed but emits no bootstrap guidance for that consumer

#### Scenario: Environment-only session
- **WHEN** a matching bootstrap hook fires during environment maintenance
- **THEN** it supplies the bootstrap instruction without activating TDD, BDD, or their input questions

### Requirement: Hook guidance uses fresh Python conditions

Event-matched, non-excluded traits SHALL support an optional top-level Python when string through profile-skill-bundles. Dispatch SHALL bind the event's invocation cwd/environment, enclosing Git root including worktrees, and effective runtime vars. Change layers SHALL participate only with an explicit caller selector. Omission SHALL be unconditional; guarded bodies SHALL participate only when the result is Boolean true.

Results SHALL be fresh without persistence or cross-call caching. False SHALL omit only that trait, preserving other guidance and generic registrations. Variable keys SHALL NOT shadow capability names or fabricate probe results. Syntax/name/non-Boolean errors, unavailable required context, and probe failures SHALL be diagnostics without successful partial output. No consumer or no eligible contribution SHALL execute no condition. Markers SHALL NOT establish index health. Conditions SHALL retain the foundation's trusted-rule contract without an isolation guarantee.

#### Scenario: Executable without local marker
- **WHEN** a trait requires which('codegraph') is not None and (git_root / '.codegraph').is_dir() but the directory is absent
- **THEN** it is omitted without suppressing unguarded bootstrap or changing registrations

#### Scenario: Availability changes during a session
- **WHEN** a tool/marker is added between matching callbacks
- **THEN** the next evaluation observes it without sync, reinstall, or reuse of the prior result

#### Scenario: Service readiness is false
- **WHEN** zmem service doctor returns valid object JSON with ok=false
- **THEN** the expression testing .get('ok') is True omits only that trait

#### Scenario: Service probe fails
- **WHEN** an eligible run_json call times out, exits nonzero, or returns invalid JSON
- **THEN** dispatch reports its diagnostic rather than readiness false or successful partial output

#### Scenario: Runtime value affects selection
- **WHEN** vars is read with an explicitly selected change supplying the winning runtime value
- **THEN** it follows runtime precedence without unrelated skill questions

#### Scenario: Ineligible event
- **WHEN** a trait is excluded from the invoked callback
- **THEN** its condition is not executed and other guidance remains eligible

### Requirement: Powerspec owns portable hook selection

Powerspec SHALL define logical hook selectors, agent-qualified native selectors, and exclusions prefixed with ~ on runtime traits. Powerspec SHALL own their mapping to native callbacks and agent response serialization; ZuAT SHALL manage the generated native assets. A supported context-delivery mapping SHALL require that the selected callback can actually deliver guidance to the agent. Unsupported mappings SHALL be reported rather than fabricated. For each trait, positive selectors SHALL be expanded before exclusions are applied. An agent-qualified negative selector SHALL exclude only the named native callback for that trait. It SHALL NOT suppress other traits, other callbacks for the same logical event, or the generic dispatcher registration. Each supported native mapping SHALL be verified for its event semantics and actual context delivery before the adapter claims support.

#### Scenario: Native callback cannot deliver context
- **WHEN** a native callback can run commands but cannot deliver the intended guidance
- **THEN** the adapter does not claim it fulfills the logical context-delivery event solely because the command executed

#### Scenario: One trait excludes a callback shared by another
- **WHEN** two active traits match a native callback and only one excludes it
- **THEN** dispatch omits the excluding trait's body and still returns the other trait's guidance
- **AND** the generic callback registration remains unchanged

#### Scenario: Logical event has multiple native mappings
- **WHEN** a trait selects a logical event and excludes one of its mapped native callbacks
- **THEN** that trait remains eligible on the other mapped callbacks

#### Scenario: All contributions are excluded
- **WHEN** no active trait contributes guidance for an invoked native callback
- **THEN** the generic dispatcher returns no guidance without uninstalling or disabling the callback

#### Scenario: Bootstrap guidance at session start
- **WHEN** a supported session-start callback fires for a consumer selecting the bootstrap trait
- **THEN** the dispatcher returns its bootstrap reminder without waiting for compaction or activating TDD

#### Scenario: Bootstrap guidance after compaction
- **WHEN** a supported post-compaction context-delivery callback fires for that consumer
- **THEN** the dispatcher returns the bootstrap reminder again using the current effective consumer configuration

### Requirement: Provision generic user-level hook dispatchers through ZuAT

Powerspec provisioning SHALL install generic pspec hook command registrations on the explicitly selected agent's supported user-level hook surfaces through ZuAT. Registrations SHALL carry the native context needed to select guidance at invocation rather than embedding one consumer's profile or trait body. Unsupported surfaces SHALL be reported without guessing native events or falling back to repository-local installation. Repeated provisioning SHALL preserve unrelated hooks/settings, reuse matching registrations, and report modified or unmanaged conflicts without silently overwriting them. Guidance selection SHALL remain a trait-level concern.

#### Scenario: Repeated dispatcher provisioning
- **WHEN** the selected agent already has matching Powerspec hook registrations alongside unrelated hooks
- **THEN** provisioning preserves unrelated entries and does not duplicate Powerspec callbacks

#### Scenario: Consumer changes its selected hook traits
- **WHEN** a consumer changes profile selection after user-level hooks have been installed
- **THEN** subsequent callbacks resolve that consumer's new effective hook traits without rewriting shared registrations

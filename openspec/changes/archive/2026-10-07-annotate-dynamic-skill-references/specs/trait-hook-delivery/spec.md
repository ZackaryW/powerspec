# Spec Delta

## MODIFIED Requirements

### Requirement: Bootstrap discovery uses runtime trait guidance

Runtime guidance SHALL introduce dynamic-resolution requirements only alongside the eligible messages that mention the affected skills. The global builtin profile SHALL NOT deliver a universal instruction to resolve every skill before native use. The ordinary pspec-skill-bootstrap helper SHALL remain available to explain a targeted content handoff without becoming a prerequisite for all skills. Existing builtin trait references to that helper SHALL be revised so ordinary skill mentions do not direct agents through Powerspec. The former builtin skill-bootstrap trait, if selected by an existing profile, SHALL emit no universal pre-skill instruction and SHALL remain a harmless compatibility resource during this migration.

Hook selectors and authored guidance SHALL remain trait-owned. Supported native hooks SHALL invoke pspec resolve hook <event> at the existing sessionStart and afterCompaction boundaries. Documentation and validation SHALL distinguish installation, hook invocation, context delivery, agent adherence, and skill execution. Installing, dispatching, classifying, or resolving guidance SHALL NOT claim that its workflow ran.

#### Scenario: Installed but unused
- **WHEN** the bundle's skills have been installed but the session never invokes them
- **THEN** no testing workflow is activated and installation reports only availability

#### Scenario: Ordinary prompt does not bootstrap again
- **WHEN** an established Codex or Claude conversation submits another ordinary prompt
- **THEN** Powerspec does not invoke sessionStart merely to repeat skill-resolution guidance

#### Scenario: Ordinary skill is mentioned
- **WHEN** an eligible trait mentions a catalog skill known to have no manifest
- **THEN** its message directs ordinary native use without requiring a Powerspec call or a preliminary null result

#### Scenario: Former bootstrap trait is explicitly selected
- **WHEN** a consumer still selects the builtin skill-bootstrap trait by its existing identity
- **THEN** that compatibility resource emits no universal pre-skill lookup instruction

### Requirement: Hook dispatch resolves the invoking consumer

Hook dispatch SHALL use the hook command's process working directory and the nearest owning OpenSpec consumer within its enclosing Git boundary, including worktrees. That invocation directory SHALL also supply the cwd used for runtime condition evaluation. Standard input SHALL NOT supply consumer location, event identity, variable values, or user answers. It SHALL select matching runtime traits from that consumer's effective profiles and return guidance in a form supported by the invoking agent. Dispatcher plumbing SHALL NOT publish context attachments, resolve skill inputs, prompt for skill choices, execute skills, discover native skill installations, or mutate project/installation state. If returned guidance calls for a user decision, that request SHALL be delivered to the agent as stdout context; the hook command SHALL NOT collect an answer or wait for one. Trusted condition calls SHALL follow the separate capability contract without a claim of isolation or rollback. An absent consumer or no matching active trait SHALL yield no guidance. Malformed nearest configuration SHALL be diagnosed rather than falling through to another consumer.

Eligible trait bodies SHALL receive the same explicit-reference classification and per-message dynamic-resolution heading semantics as generated context attachments. Classification SHALL follow event matching and condition eligibility, inspect only metadata needed for eligible referenced names, and SHALL NOT evaluate skill inputs or dynamic content. Runtime metadata inspection SHALL use available bundled/local resources and bounded read-only lookup of already-materialized remote resources. It SHALL NOT acquire, refresh, install, or repair sources, binaries, or skills. Repeated names and source lookups SHALL be deduplicated within one dispatch. No eligible skill mentions SHALL mean no remote metadata inspection for annotation purposes.

An operational failure to obtain remote metadata, including absence or timeout, SHALL leave the affected classification explicitly unknown, identify the affected skill in its delivered message, and report a diagnostic separately from the native stdout envelope. Unknown SHALL NOT be reported as ordinary or dynamically resolved. The message SHALL direct the agent to inspect the skill selected through its native integration and request Powerspec assembly only if that selected copy has a manifest. Unknown metadata SHALL NOT suppress independent eligible guidance. A missing name after successful inspection, a malformed readable manifest, or conflicting known classifications SHALL remain an authored-resource error without successful partial guidance. The existing five-second native handler limit SHALL remain unchanged; metadata inspection SHALL have a smaller finite budget and use the unknown fallback when it is exhausted.

#### Scenario: Shared dispatcher serves different projects
- **WHEN** the same user-level dispatcher is invoked from two consumers with different effective hook traits
- **THEN** each receives guidance selected from its own process working directory and configuration without reinstalling hooks

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

### Requirement: Powerspec owns portable hook selection

Powerspec SHALL define logical hook selectors, agent-qualified native selectors, and exclusions prefixed with ~ on runtime traits. Powerspec SHALL own their mapping to native callbacks and agent response serialization; ZuAT SHALL manage the generated native assets. A supported context-delivery mapping SHALL require that the selected callback can actually deliver guidance to the agent. Unsupported mappings SHALL be reported rather than fabricated. For each trait, positive selectors SHALL be expanded before exclusions are applied. An agent-qualified negative selector SHALL exclude only the named native callback for that trait. It SHALL NOT suppress other traits, other callbacks for the same logical event, or the generic dispatcher registration.

Codex sessionStart SHALL map only to native SessionStart sources startup and clear; Claude sessionStart SHALL map only to startup, clear, and fork. Both agents' afterCompaction SHALL map to the verified native context-delivery callback for compact. Powerspec SHALL NOT register callbacks for native resume, UserPromptSubmit, PreToolUse, PostToolUse, PermissionRequest, Stop, subagent, or session-end events. Each supported native mapping SHALL be verified for its event semantics and actual context delivery before the adapter claims support.

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
- **THEN** the generic callback returns no guidance without uninstalling or disabling the registration

#### Scenario: Ordinary Codex turn is represented as resume
- **WHEN** Codex emits native SessionStart with source resume while submitting another turn
- **THEN** no Powerspec callback matches and no runtime condition or service doctor is executed

#### Scenario: Bootstrap guidance at session start
- **WHEN** startup or clear establishes context for a consumer with eligible messages mentioning dynamic skills
- **THEN** the dispatcher returns targeted dynamic-resolution headings with those messages without a universal pre-skill lookup or activation of TDD

#### Scenario: Bootstrap guidance after compaction
- **WHEN** a supported compact context-delivery callback fires for that consumer
- **THEN** the dispatcher restores the eligible targeted headings using current consumer configuration and metadata without adding a universal lookup requirement

### Requirement: Hook guidance uses fresh Python conditions

Event-matched, non-excluded traits SHALL support an optional top-level Python when string through profile-skill-bundles. Dispatch SHALL bind the event's invocation cwd/environment, enclosing Git root including worktrees, and effective runtime vars. Change layers SHALL participate only with an explicit caller selector. Omission SHALL be unconditional; guarded bodies SHALL participate only when the result is Boolean true.

Results SHALL be fresh at each matched Powerspec lifecycle boundary without persistence or cross-call caching. False SHALL omit only that trait, preserving other guidance and generic registrations. Variable keys SHALL NOT shadow capability names or fabricate probe results. Syntax/name/non-Boolean errors and unavailable required context SHALL be diagnostics without successful partial output. An operational run_json failure SHALL be diagnosed and omit only its owning optional trait while preserving successfully resolved unrelated trait guidance. No consumer or no eligible contribution SHALL execute any condition. Markers SHALL NOT establish index health. Conditions SHALL retain the foundation's trusted-rule contract without an isolation guarantee.

#### Scenario: Executable without local marker
- **WHEN** a trait requires which('codegraph') is not None and (git_root / '.codegraph').is_dir() but the directory is absent
- **THEN** it is omitted without suppressing unrelated unguarded guidance or changing registrations

#### Scenario: Availability changes during a session
- **WHEN** a tool or marker is added after one matched callback and before a later startup, clear, fork, or compaction callback
- **THEN** the later evaluation observes it without sync, reinstall, or reuse of the prior result

#### Scenario: Service readiness is false
- **WHEN** zmem service doctor returns valid object JSON with ok=false
- **THEN** the expression testing .get('ok') is True omits only the Zmem trait

#### Scenario: Service probe fails
- **WHEN** the Zmem trait's eligible run_json call times out, exits nonzero, or returns invalid JSON
- **THEN** dispatch reports the Zmem diagnostic, omits its guidance, and still returns unrelated successfully resolved guidance

#### Scenario: Runtime value affects selection
- **WHEN** vars is read with an explicitly selected change supplying the winning runtime value
- **THEN** it follows runtime precedence without unrelated skill questions

#### Scenario: Ineligible event
- **WHEN** a trait is excluded from the invoked callback or no Powerspec callback is mapped to the native event
- **THEN** its condition is not executed and other guidance remains eligible at their own matched boundaries

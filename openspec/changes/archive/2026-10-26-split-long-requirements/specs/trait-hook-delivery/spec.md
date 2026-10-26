## MODIFIED Requirements

### Requirement: Bootstrap discovery uses runtime trait guidance

Runtime guidance SHALL introduce dynamic-resolution requirements only alongside eligible messages mentioning the affected skills, and the global builtin profile SHALL NOT deliver a universal resolve-every-skill instruction. The ordinary pspec-skill-bootstrap helper SHALL stay available to retrieve a needed pspec: target and explain a targeted native handoff without becoming a prerequisite for all skills, and builtin traits SHALL NOT route ordinary skill mentions through it.

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

#### Scenario: Explicit namespace reminder at startup
- **WHEN** a supported startup callback runs for a consumer retaining the builtin profile and bootstrap skill
- **THEN** the delivered context identifies pspec: as a trigger for bootstrap without resolving a target skill or probing every catalog resource

#### Scenario: Restore namespace reminder after compaction
- **WHEN** the supported afterCompaction callback runs for the same consumer
- **THEN** the compact routing reminder is restored using current effective selection

#### Scenario: Bootstrap is excluded
- **WHEN** the effective bundle no longer selects bootstrap
- **THEN** its routing trait contributes no instruction to invoke the absent skill and no shared hook registration is removed

#### Scenario: Ordinary prompt uses delivered routing knowledge
- **WHEN** the user mentions pspec:helper later in the established session
- **THEN** the agent can invoke bootstrap from the earlier reminder without adding a per-prompt native callback

#### Scenario: Scenario guidance is sufficient to select a target
- **WHEN** a later task matches a delivered rule calling for pspec:A without the user naming A
- **THEN** the guidance supports retrieval of A through bootstrap without an additional lifecycle callback or preloading B/C

#### Scenario: Startup preserves deferred procedure boundaries
- **WHEN** A, B, and C are selected through resolve-skills and no matching task scenario has occurred
- **THEN** startup and compaction restore only the routing reminder and lightweight owning rules, with no A/B/C procedure bodies or new procedure-resolution calls

#### Scenario: More unused targets do not expand routing context
- **WHEN** additional resolve-only skills are selected without changing applicable scenario rules
- **THEN** the bootstrap routing reminder remains the same compact instruction rather than listing their names, descriptions, or procedures

### Requirement: Hook dispatch resolves the invoking consumer

Hook dispatch SHALL use the hook process's working directory, also the condition cwd, and its nearest owning consumer within the Git boundary, including worktrees. Stdin SHALL NOT supply consumer location, event identity, variable values or user answers. It SHALL select matching runtime traits from the consumer's effective profiles and return agent-supported guidance. An absent consumer or no matching trait SHALL yield no guidance; malformed nearest configuration SHALL be diagnosed.

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

### Requirement: Hook guidance uses fresh Python conditions

Event-matched, non-excluded traits SHALL support an optional top-level Python when string through profile-skill-bundles. Dispatch SHALL bind the invocation cwd and environment, enclosing Git root including worktrees, and effective runtime vars, with change layers only under an explicit selector. Omission SHALL be unconditional; guarded bodies SHALL participate only on Boolean true. Results SHALL be fresh at each matched boundary, never persisted or cached, and false SHALL omit only that trait.

#### Scenario: Executable without local marker
- **WHEN** a trait requires which('codegraph') is not None and (git_root / '.codegraph').is_dir() but the directory is absent
- **THEN** it is omitted without suppressing unrelated unguarded guidance or changing registrations

#### Scenario: Availability changes during a session
- **WHEN** a tool or marker is added after one matched callback and before a later startup, clear, fork, or compaction callback
- **THEN** the later evaluation observes it without sync, reinstall, or reuse of the prior result

#### Scenario: Service readiness is false
- **WHEN** an optional service-health trait probes a service that returns valid object JSON with ok=false
- **THEN** the expression testing .get('ok') is True omits only that guarded trait; the unconditional standing memory rule remains eligible

#### Scenario: Service probe fails
- **WHEN** an optional service-health trait's eligible run_json call times out, exits nonzero, or returns invalid JSON
- **THEN** dispatch reports the optional trait diagnostic, omits that guarded guidance, and still returns independent guidance including the unconditional standing memory rule

#### Scenario: Runtime value affects selection
- **WHEN** vars is read with an explicitly selected change supplying the winning runtime value
- **THEN** it follows runtime precedence without unrelated skill questions

#### Scenario: Ineligible event
- **WHEN** a trait is excluded from the invoked callback or no Powerspec callback is mapped to the native event
- **THEN** its condition is not executed and other guidance remains eligible at their own matched boundaries

### Requirement: Powerspec owns portable hook selection

Powerspec SHALL define logical hook selectors, agent-qualified native selectors and ~-prefixed exclusions on runtime traits, and own their mapping to native callbacks and response serialization, while ZuAT manages the generated native assets. A context-delivery mapping SHALL require that the callback can deliver guidance, and unsupported mappings SHALL be reported. Positive selectors SHALL expand before exclusions, and an agent-qualified exclusion SHALL remove only that callback for that trait.

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

### Requirement: Provision generic user-level hook dispatchers through ZuAT

Provisioning SHALL install generic `pspec resolve hook` registrations on the selected agent's supported user-level hook surfaces through ZuAT, each advisory handler having an explicit timeout of at most five seconds and a concise status. Registrations SHALL carry the native context to select guidance at invocation, not one consumer's profile or trait body, and SHALL NOT return a blocking host decision.

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

### Requirement: Native matchers own event source filtering

Installed native matchers SHALL select which supported lifecycle callbacks invoke Powerspec, and the command's event and agent arguments SHALL select the mapping without inspecting stdin to revalidate native event names or sources. Direct invocation of a supported logical event SHALL resolve its guidance without claiming a native event occurred. Existing mappings, forbidden high-frequency registrations, five-second handler timeouts and per-trait exclusions SHALL remain in force.

#### Scenario: Resume does not start Powerspec
- **WHEN** the native host emits SessionStart with source resume
- **THEN** no installed Powerspec matcher selects it and no Powerspec condition or doctor runs for that event

#### Scenario: Compaction maps through arguments
- **WHEN** the compact matcher invokes `pspec resolve hook afterCompaction --agent codex`
- **THEN** Powerspec selects afterCompaction guidance and emits the supported SessionStart additional-context response without inspecting a native source field

#### Scenario: Direct inspection of guidance
- **WHEN** a caller explicitly runs `pspec resolve hook sessionStart --agent claude` in a configured consumer
- **THEN** the command returns applicable guidance without requiring proof of a native SessionStart event and without claiming the agent followed it

### Requirement: Standing memory guidance survives unavailable tooling

The selected zmem standing rule SHALL be unconditional at existing startup and compaction boundaries, visible without a successful service probe. It SHALL direct agents to report unavailable memory tooling and use Git and current-source evidence with that limitation, rather than claim a memory check or wait for permission for authorized investigation. Missing remote skill metadata SHALL keep the explicit unknown fallback, and no prompt/tool callback or automatic repair SHALL be added.

#### Scenario: Missing or unhealthy zmem
- **WHEN** zmem is missing, unhealthy or cannot be probed
- **THEN** both delivery events still produce the standing rule and its explicit fallback instructions

#### Scenario: Sources have not been initialized
- **WHEN** remote zmem skill metadata has no selected materialization
- **THEN** runtime output retains the rule with unknown classification and performs no acquisition

## ADDED Requirements

### Requirement: Bootstrap trait delivers one compact reminder

The builtin profile SHALL select the skill-bootstrap runtime trait. At supported sessionStart and afterCompaction boundaries it SHALL deliver one compact reminder to use bootstrap when a user request or applicable scenario needs a pspec: target, without a repeated skill-name mention. The reminder SHALL be guarded by effective selection of the bootstrap skill and SHALL be the same narrowly scoped reminder for every profile selecting the trait.

#### Scenario: No repeated skill-name mention needed
- **WHEN** applicable scenario guidance already calls for a pspec: target
- **THEN** the reminder lets the agent use bootstrap without the user naming the skill again

#### Scenario: Other profiles get the same reminder
- **WHEN** a profile other than the builtin one selects the bootstrap trait
- **THEN** it receives the same narrowly scoped reminder, not a universal pre-skill instruction

### Requirement: Bootstrap reminder stays compact

The bootstrap reminder SHALL contain no full skill inventory, target discovery descriptions, procedure bodies or complete routing procedure, and SHALL NOT request resolution of ordinary native skills. Selecting more unused resolve-only skills SHALL NOT expand it into an inventory or start procedural resolution. Lightweight scenario rules SHALL keep their conditions and target references without embedding target procedures.

#### Scenario: Reminder carries no inventory
- **WHEN** the bootstrap reminder is delivered
- **THEN** it lists no skill inventory, discovery descriptions or procedure bodies

#### Scenario: Scenario rule keeps only its reference
- **WHEN** a lightweight scenario rule names a pspec: target
- **THEN** it keeps its condition and reference without embedding that target's procedure

### Requirement: Hook delivery claims stay separate from execution

Hook selectors and authored guidance SHALL remain trait-owned, and supported native hooks SHALL invoke pspec resolve hook <event> at the sessionStart and afterCompaction boundaries. Documentation and validation SHALL distinguish installation, hook invocation, context delivery, agent adherence and skill execution; installing, dispatching, classifying or resolving guidance SHALL NOT claim that its workflow ran.

#### Scenario: Hooks call the resolve command
- **WHEN** a supported native sessionStart or afterCompaction hook fires
- **THEN** it invokes pspec resolve hook with that logical event

#### Scenario: Delivery is not execution
- **WHEN** guidance has been installed, dispatched or resolved
- **THEN** Powerspec does not report that the guided workflow ran

### Requirement: Hook dispatch has no side effects

Dispatcher plumbing SHALL NOT publish context attachments, resolve skill inputs, prompt for skill choices, execute skills, discover native skill installations or mutate project or installation state. Guidance requesting a user decision SHALL be delivered as stdout context without collecting or waiting for an answer. Trusted condition calls SHALL follow the separate capability contract without a claim of isolation or rollback.

#### Scenario: Dispatch writes nothing
- **WHEN** a hook dispatch completes
- **THEN** no project, configuration or installation file was changed

#### Scenario: Dispatch does not wait for answers
- **WHEN** delivered guidance asks the user to decide something
- **THEN** the hook command exits after delivering it without reading an answer

### Requirement: Trait bodies get the same skill classification as contexts

Eligible trait bodies SHALL get the same reference classification and per-message dynamic-resolution headings as context attachments, after event and condition eligibility, inspecting only eligible referenced names' metadata and never evaluating skill inputs or dynamic content. Metadata SHALL come from bundled or local resources and bounded read-only lookup of materialized remote resources, without acquiring, refreshing, installing or repairing anything, deduplicated within one dispatch.

#### Scenario: No mentions, no metadata lookup
- **WHEN** no eligible trait body mentions a skill
- **THEN** dispatch performs no remote metadata inspection for annotations

#### Scenario: Repeated names are looked up once
- **WHEN** several eligible traits mention the same remote skill
- **THEN** its metadata is looked up once within that dispatch

### Requirement: Unavailable remote metadata is reported as unknown

When remote metadata cannot be obtained, including absence or timeout, the classification SHALL be explicitly unknown, never ordinary or dynamic. The delivered message SHALL name the skill and direct the agent to request Powerspec assembly only if its native-selected copy has a manifest, with a diagnostic outside the stdout envelope. Unknown metadata SHALL NOT suppress other eligible guidance. Metadata inspection SHALL use a finite budget smaller than the unchanged five-second handler limit.

#### Scenario: Unknown does not suppress other guidance
- **WHEN** one mentioned skill's metadata is unknown
- **THEN** other eligible guidance in the same dispatch is still delivered

#### Scenario: Authored metadata errors still fail
- **WHEN** inspection succeeds but the name is missing, a readable manifest is malformed, or known classifications conflict
- **THEN** dispatch reports an authored-resource error without successful partial guidance

### Requirement: Hook condition failures stay contained

Variable keys SHALL NOT shadow capability names or fabricate probe results. Syntax, name or non-Boolean errors and unavailable required context SHALL be diagnostics without partial output, while an operational run_json failure SHALL omit only its owning optional trait. No consumer or no eligible contribution SHALL execute any condition. Markers SHALL NOT establish index health, and conditions SHALL keep the trusted-rule contract without an isolation guarantee.

#### Scenario: Variable cannot shadow a capability
- **WHEN** a runtime variable has the same name as a condition capability
- **THEN** the capability keeps its meaning and no probe result is fabricated

#### Scenario: Nothing eligible runs no condition
- **WHEN** there is no consumer or no eligible contribution for the event
- **THEN** no condition is executed

#### Scenario: Condition error yields no partial output
- **WHEN** a condition has a syntax, name or non-Boolean error
- **THEN** dispatch reports a diagnostic and returns no partial guidance

### Requirement: Native event mappings are fixed and verified

Codex sessionStart SHALL map only to native SessionStart sources startup and clear, and Claude sessionStart only to startup, clear and fork; both agents' afterCompaction SHALL map to the verified context-delivery callback for compact. Powerspec SHALL NOT register native resume, UserPromptSubmit, PreToolUse, PostToolUse, PermissionRequest, Stop, subagent or session-end callbacks, and SHALL verify each mapping's semantics and context delivery before claiming support.

#### Scenario: Claude fork starts a session
- **WHEN** Claude starts a forked session
- **THEN** its sessionStart guidance is delivered, while Codex has no fork mapping

#### Scenario: High-frequency events are never registered
- **WHEN** hooks are provisioned for any supported agent
- **THEN** no prompt, tool, permission, stop, subagent or session-end callback is registered

### Requirement: Hook reconciliation preserves foreign callbacks

Repeated provisioning SHALL preserve unrelated hooks and settings, reuse matching registrations, and report modified or unmanaged conflicts without overwriting them. Reconciliation SHALL replace safely owned earlier Powerspec registrations, including legacy aliases and broader resume matchers, without duplicates, and SHALL NOT remove or rewrite callbacks owned by another tool. Guidance selection SHALL remain a trait-level concern.

#### Scenario: Another tool's callback survives
- **WHEN** the hook settings contain a callback owned by another tool
- **THEN** provisioning leaves it in place unchanged

#### Scenario: No duplicate callbacks after migration
- **WHEN** an owned legacy Powerspec registration is replaced
- **THEN** only the current registration remains

### Requirement: Hook provisioning inspects completely before mutation

Provisioning SHALL require complete inspection before any mutation. Current owned source-matching hooks SHALL be reused, safely outdated owned hooks updated without force, exact unowned source-matching groups adopted without rewriting bytes, and only verified absent groups installed. Indeterminate, unsupported, ambiguous or conflicting groups SHALL fail with diagnostics and no installation fallback.

#### Scenario: Outdated owned hook is updated
- **WHEN** an owned hook group is unmodified but older than the desired source
- **THEN** provisioning updates it without requiring force

#### Scenario: Only absent groups are installed
- **WHEN** inspection verifies that no hook group exists yet
- **THEN** provisioning installs it, and installs nothing when inspection is incomplete

### Requirement: Hook receipt repair is narrow

Explicit hook repair SHALL permit only a valid owned receipt conflict whose uniquely identified native group already matches the desired source, using ZuAT's targeted recoverable update that preserves native bytes and modification time and keeps the recovery operation identifier. It SHALL NOT permit replacing edited content, positional overwrites, duplicate candidates, invalid receipts or cross-provider targets.

#### Scenario: Repair keeps the operation identifier
- **WHEN** an explicit repair succeeds
- **THEN** the recovery operation identifier is reported and native bytes and modification time are unchanged

#### Scenario: Invalid receipt is not repaired
- **WHEN** the ownership receipt is invalid or names another provider's target
- **THEN** repair fails without changing the hooks

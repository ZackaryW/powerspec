# Spec Delta

## MODIFIED Requirements

### Requirement: Bootstrap discovery uses runtime trait guidance

Runtime guidance SHALL introduce dynamic-resolution requirements only alongside the eligible messages that mention the affected skills. The global builtin profile SHALL NOT deliver a universal instruction to resolve every skill before native use. The ordinary pspec-skill-bootstrap helper SHALL remain available to retrieve a needed pspec: target named by the user or applicable scenario guidance and explain a targeted native content handoff without becoming a prerequisite for all skills. Existing builtin trait references to that helper SHALL be revised so ordinary skill mentions do not direct agents through Powerspec. The builtin profile SHALL select the skill-bootstrap runtime trait. At existing supported sessionStart and afterCompaction boundaries, that trait SHALL deliver one compact reminder to use bootstrap when a user request or applicable task scenario needs a pspec: target, without requiring a repeated user skill-name mention. Its reminder SHALL be guarded by effective selection of the bootstrap skill, SHALL contain no full skill inventory, target discovery descriptions, procedure bodies, or complete routing procedure, and SHALL not request resolution of ordinary native skills. Existing profiles selecting that trait SHALL receive the same narrowly scoped reminder, not a universal pre-skill instruction. Selecting more unused resolve-only skills SHALL NOT by itself expand this reminder into a catalog inventory or initiate procedural resolution. Lightweight scenario rules SHALL retain their conditions and target references without embedding the target procedures.

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


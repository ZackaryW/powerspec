# Profile Skill Bundles Delta

## MODIFIED Requirements

### Requirement: Command JSON conditions distinguish data from probe failures

run_json SHALL accept a nonempty list of string argv items, execute without a shell in the invocation cwd/environment, and return stdout parsed as a JSON object after exit zero. Its default subprocess timeout SHALL be five seconds. A caller operating under a shorter externally enforced deadline SHALL be able to supply a finite positive timeout no greater than that default; runtime hook delivery SHALL use a timeout short enough to leave cleanup and serialization time before its native callback deadline. Invalid arguments, missing executables, nonzero exits, timeout, invalid JSON, and non-object JSON SHALL produce diagnostics instead of readiness false or successful condition output. A valid object SHALL remain data for the expression to assess; process success alone SHALL NOT imply readiness. The helper timeout SHALL NOT be advertised as a complete expression execution limit.

#### Scenario: Service doctor reports a problem
- **WHEN** zmem service doctor exits zero with ok=false and the expression tests .get('ok') is True
- **THEN** run_json returns the object and the condition evaluates false

#### Scenario: Missing ok field
- **WHEN** a successful probe returns an object without ok and the expression tests .get('ok') is True
- **THEN** the condition evaluates false without inventing positive readiness

#### Scenario: Hook boundary supplies a smaller budget
- **WHEN** runtime hook delivery evaluates run_json under a five-second native callback deadline
- **THEN** the subprocess receives a smaller positive timeout and leaves time for the dispatcher to diagnose or serialize its result

#### Scenario: Probe cannot produce data
- **WHEN** a probe times out, exits nonzero, or produces invalid or non-object JSON
- **THEN** evaluation diagnoses the probe and resource instead of treating failure as normal false

### Requirement: Conditions execute only at their owning boundary

The foundation SHALL expose condition evaluation separately from composition. Eligible contributions SHALL be evaluated once per owning invocation with fresh namespaces and current capability context. Python calls SHALL retain authored order without implicit probe caching. Results SHALL NOT be persisted or reused across invocations.

Sync SHALL evaluate contexts while compiling a snapshot valid until another sync. Hooks SHALL evaluate matching non-excluded traits only at mapped Powerspec lifecycle callbacks. False SHALL omit only its contribution without removing other guidance, skills, or native registrations. Context publication and configuration or expression authoring errors SHALL remain atomic and yield no successful partial result. Runtime hook delivery MAY isolate an operational command-probe failure to its owning optional trait when it reports the diagnostic and preserves independent successfully resolved traits. Composition, native events without a Powerspec mapping, and ineligible contributions SHALL execute no conditions.

#### Scenario: Composition is machine-independent
- **WHEN** profiles with conditional contexts or traits are composed
- **THEN** expressions are retained without observations or subprocess execution

#### Scenario: Later calls observe availability
- **WHEN** a tool becomes available between matched runtime lifecycle callbacks
- **THEN** the later callback observes it without synchronization or a cached earlier result

#### Scenario: Ordinary prompt has no owning Powerspec boundary
- **WHEN** an established session receives an ordinary prompt without startup, clear, fork, or compact
- **THEN** no selected context or trait condition is evaluated

#### Scenario: False affects one contribution
- **WHEN** one condition returns false and another contribution is unconditional
- **THEN** only the guarded contribution is omitted, preserving skills and shared registrations

#### Scenario: Runtime probe failure is isolated
- **WHEN** an optional runtime trait's command probe fails after another trait resolves successfully
- **THEN** hook delivery diagnoses and omits the failing trait while retaining the independent guidance

#### Scenario: Error is not omission
- **WHEN** an eligible expression has invalid syntax, an unavailable required binding, or a non-Boolean result
- **THEN** the caller receives a resource-specific diagnostic instead of treating the authored error as normal false

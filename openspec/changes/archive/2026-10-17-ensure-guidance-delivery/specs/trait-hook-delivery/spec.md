## ADDED Requirements

### Requirement: Standing memory guidance survives unavailable tooling
The selected zmem standing rule SHALL be unconditional at existing startup and compaction boundaries. It SHALL NOT require a successful service probe to remain visible. It SHALL direct agents to report unavailable memory tooling and use Git/current-source evidence with that limitation, rather than claim a memory check or wait for permission for the authorized investigation. Missing remote skill metadata SHALL retain the existing explicit unknown-classification fallback. No prompt/tool callback or automatic service repair SHALL be added.

#### Scenario: Missing or unhealthy zmem
- **WHEN** zmem is missing, unhealthy or cannot be probed
- **THEN** both delivery events still produce the standing rule and its explicit fallback instructions

#### Scenario: Sources have not been initialized
- **WHEN** remote zmem skill metadata has no selected materialization
- **THEN** runtime output retains the rule with unknown classification and performs no acquisition

## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Lifecycle commands expose active work while waiting
Init, including source-only init, and upgrade SHALL emit default progress on stderr before potentially blocking work and report completed item outcomes as they occur. Messages SHALL identify consumer setup, manager preparation, source identity and known stage, individual skill identity and known item count, hooks, and selection publication or removal/recovery when reached. The innermost active stage SHALL report elapsed waiting at five-second intervals during a blocked operation. Waiting SHALL NOT claim confirmed upstream activity, measured transfers or completion percentages. Successful results SHALL retain their stdout and exit contracts, and progress SHALL NOT activate for unrelated JSON or resolution protocols.

#### Scenario: Native source operation takes time
- **WHEN** init waits on Saucepan to prepare a selected source
- **THEN** stderr identifies that source before the wait and continues reporting the active stage and elapsed waiting without requiring native output

#### Scenario: Earlier item fails
- **WHEN** one skill has a returned ownership conflict and later skills remain to be checked
- **THEN** the conflict is reported before the later checks finish, without claiming ownership or successful completion

#### Scenario: Source-only initialization
- **WHEN** init runs without an agent and prepares sources
- **THEN** source progress is visible without installing agent assets

#### Scenario: Redirected command output
- **WHEN** stdout and stderr are redirected to separate streams
- **THEN** readable progress remains on stderr and stdout retains only its existing results

### Requirement: Progress observation preserves failure and recovery boundaries
Progress SHALL stop when an operation completes, fails or is interrupted, without emitting a later waiting event for that completed stage. Failures and timeouts SHALL identify the active operation and elapsed time while preserving original diagnostics, nonzero exit behavior and applicable retry/pending-state guidance. A heartbeat SHALL NOT extend deadlines, retry mutations, change source selection, bypass native ownership or assert rollback. Library calls without a progress observer SHALL remain silent.

#### Scenario: Source request times out
- **WHEN** source preparation reports a timeout after starting a mutation
- **THEN** the command identifies the failed source stage and elapsed wait, reports the existing uncertain-state guidance and leaves pending receipts governed by the existing retry contract

#### Scenario: Completed or interrupted operation
- **WHEN** an operation exits normally or through interruption
- **THEN** its progress worker shuts down and no later waiting line is emitted for it

#### Scenario: Protocol invocation
- **WHEN** a caller resolves hook or skill guidance or requests doctor JSON
- **THEN** lifecycle progress does not pollute the response

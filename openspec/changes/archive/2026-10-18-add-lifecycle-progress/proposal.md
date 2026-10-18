# Proposal

## Why

Init and upgrade can block on manager preparation, source materialization and native provisioning for minutes before printing any result. Users cannot identify the active operation or distinguish a responsive caller from confirmed upstream progress.

## What Changes

- Emit immediate stage and per-item outcomes on stderr for init and upgrade, including source-only init.
- Emit a five-second heartbeat identifying the active operation and elapsed time during waits, without claiming measured transfer progress.
- Keep successful stdout results, exit behavior, ownership checks, source selection and recovery semantics intact.
- Provide contextual failure/timeout messages and document progress evidence limits.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli-product-surface`: Observable progress for long-running lifecycle commands with clean result streams.

## Impact

PowerSpec CLI presentation, orchestration, source and native provisioning boundaries, plus a reusable heartbeat helper. No Rust/SDK wire changes, dependencies, force/adoption changes, or automatic retries. Active OpenSpec artifacts stay outside incremental commits.

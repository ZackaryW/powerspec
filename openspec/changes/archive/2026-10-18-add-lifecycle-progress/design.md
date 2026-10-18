# Design

## Context

See proposal.md. CLI handlers currently wait for complete installation/upgrade results before presenting individual outcomes. Source calls capture native JSON and have finite per-call timeouts, but there is no progress stream. Existing integration tests use injected stores and real native tools in isolated homes. The unrelated modified consumer .gitignore is preserved.

## Goals / Non-Goals

Goals: identify the current blocking stage, keep the caller visibly responsive, surface per-item failures before later work, and preserve final result/exit semantics.
Non-goals: native byte/transfer telemetry, proving upstream liveness, changing timeout budgets, adding retries, changing ownership/force policy, or enabling progress in machine-facing hook/skill protocols.

## Decisions

- A small optional progress observer emits start, waiting, and terminal events with elapsed seconds. One heartbeat worker per active reporting session observes the innermost active stage; it stops on all exits. Nested stages restore their parent. Terminal events cannot be followed by a stale wait event for the same stage.
- The reusable helper lives in utils/progress.py. A feature-owned progress.py binds a reporter with ContextVar only inside init/upgrade and renders plain flushed stderr lines. This avoids widening every injected source/store API and keeps direct library, doctor and protocol calls silent. Each invocation owns its own reporter; there is no process-wide singleton worker.
- Default cadence is five seconds in both interactive terminals and redirected logs. Report elapsed waiting, never percentages or inferred network progress. Source labels use aliases/references, not credential-bearing origins. Successful stdout and structured outputs retain their contracts.
- Instrument consumer setup, bundle composition, lazy manager preparation, each source preparation/materialization/validation, each native skill check (with known item count), hook reconciliation, and publication/removal/recovery stages. Source-only init uses the same path. Emit actual per-item status and diagnostics immediately on stderr, retaining existing final stdout results for callers.
- Failure events add stage and elapsed context while preserving the original exception/error code, pending receipt handling and retry instruction. A returned failure outcome is explicitly marked failed, never defaulted to done. KeyboardInterrupt stops observation and propagates; it does not introduce a new child-process cancellation promise. Observer output failures disable that observer without changing the operation result.

### Utility assessment and contract

`Progress(emit, interval=5, clock=monotonic)` is a context manager, with `stage(label)` yielding a handle whose result(status, detail) records the observed outcome. It emits immutable events containing label, state, elapsed, and optional detail. Input validation rejects nonpositive/nonfinite cadence. It runs no operation itself, performs no subprocess calls, and owns only a joined heartbeat worker. Exceptions from the operation propagate after a failed/cancelled terminal event. It is reusable for a backup/export CLI whose remote upload blocks without telemetry. A no-observer context creates no worker.

Reuse threading.Event.wait, threading locks and time.monotonic. Existing Typer supplies output; Rich spinners are available transitively but do not provide nested operation ownership, nonterminal logs or evidence semantics, and would add a direct presentation dependency for no needed capability. SDK and Zuu APIs inspected have no matching JSON-operation progress callback; keep their execution and timeout ownership intact. No new package is needed.

Verify the helper first with domain-neutral tasks: ordered events, elapsed wait updates, nested stage restoration, exceptional and cancelled exits, observer failure, and thread shutdown. Then verify application stages and actual CLI subprocess output while an isolated operation is blocked. A packaged installed command must expose progress before the operation is released.

## Risks / Trade-offs

- A heartbeat can be mistaken for upstream progress -> explicitly render waiting language and document its evidence limit.
- Concurrent output can reorder terminal messages -> serialize event emission and stage changes under the reporter's lock; close/join before returning.
- Per-item failures are returned rather than raised -> set terminal outcomes from actual provisioning results and keep later work behavior intact.
- New progress output can contaminate protocols -> activate only in human init/upgrade handlers; preserve stdout and test resolve/JSON boundaries.

## Migration Plan

No stored schema or dependency migration. Build and install the updated local package after affected checks and isolated command verification. Keep active change artifacts outside implementation checkpoints. No automatic archive, tagging, push or live forced adoption.

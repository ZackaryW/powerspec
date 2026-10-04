# Design

## Context

See proposal.md for the user-visible problem. Commit `1501872` introduced `json.load(sys.stdin)` in `src/powerspec/cli/hook.py`, with payload validation and cwd extraction in `src/powerspec/hooks.py`. The later CLI product specification made this transport mandatory. Commit `95539ba` bounded native handlers and optional probes but retained the read. Tests supply complete payloads, so they do not expose an open-pipe wait.

Current hook resolution uses native JSON only for event/source validation and cwd discovery. The installed command already carries the logical event and agent; native matchers already select the event source. The serializer does not need the incoming document. This change replaces the current CLI spec's stdin requirement; archived design documents remain historical evidence.

## Goals / Non-Goals

**Goals:**
- Make input acquisition nonblocking by eliminating stdin access entirely.
- Keep consumer discovery, condition evaluation, and catalog selection tied to one invocation cwd.
- Preserve existing output envelopes, runtime selection semantics, error isolation, and lifecycle restrictions.

**Non-Goals:**
- Add an input protocol, payload fallback, cwd option, background reader, or stdin timeout.
- Introduce a pending-question workflow or automatically resolve skill variables inside hooks.
- Change skill resolution, provisioning ownership, condition caching, or trusted-rule capabilities.
- Claim a universal five-second execution guarantee: native handler deadlines and individual probe bounds remain; arbitrary trusted rules and unrelated latency are separate concerns.

## Decisions

### Capture process cwd once at the CLI boundary

The handler captures `Path.cwd()` and passes it explicitly into dispatch, using the same directory for local catalog/consumer discovery. Dispatch accepts cwd instead of a payload and reuses existing Git-bounded discovery. Conditions receive this invocation cwd rather than the Git root or executable directory. Remove `validate_payload` and payload-only callback acceptance plumbing once callers are migrated. Preserve mapping and selector validation.

Using stdin opportunistically would retain two conflicting sources of context and reintroduce blocking risk. A timed reader or a new `--cwd` surface is unnecessary for the agreed command. Direct callers set their process working directory.

### Native registration matchers filter sources

Retain `native_document` command strings, matchers, timeout metadata, and response serialization. Matchers own startup/clear/fork/compact selection and exclude resume; the dispatcher validates supported event/agent arguments. Move tests of source filtering to generated registration behavior rather than simulating a second payload gate. A manually invoked command is an explicit guidance request, not evidence of a native event.

### Requests for decisions remain content

Guidance that asks the agent a question is ordinary additional context in stdout. The command neither prompts nor reads an answer, creates pending state, or runs the referenced skill. Existing errors remain stderr diagnostics; missing required configuration does not silently become a question or fabricated default. This requires no new question schema.

### Reuse existing APIs without new utility modules

`pathlib.Path.cwd`, existing consumer discovery, catalog composition, condition evaluation, and native serialization cover the change. No portable helper contract or third-party dependency is missing; a generic input abstraction would recreate complexity being removed. Tests use the standard library's subprocess API and existing pytest fixtures.

### Test the actual waiting boundary

Update `tests/test_hooks.py` and `tests/test_repository_investigation.py` callers to pass cwd directly. Add an in-process stdin sentinel that fails on any read, plus real CLI subprocess tests for both supported events/agents with the parent keeping stdin open. Wait for process exit with a bounded test timeout before closing stdin; do not use a helper that closes stdin first and hides the defect. Always terminate/reap only the test-owned child on timeout. Use isolated local consumers with deterministic guidance and no external probes so startup/input behavior is not confused with network latency.

Also test ignored conflicting cwd payloads and malformed input, closed stdin, invalid selectors, nested consumers/worktrees, explicit change vars, silent no-consumer/no-match, stderr error behavior, optional-probe isolation, native envelopes, and generated matcher exclusions. Reuse existing coverage where unchanged.

## Risks / Trade-offs

- Callers that supplied payload cwd from an unrelated process directory select a different consumer after this change → document migration to the actual project cwd and test that stdin cannot redirect it.
- A native host could launch commands from a different directory than the session project → verify supported Codex/Claude launches with isolated settings during implementation; report any mismatch as an adapter gap rather than restoring stdin as a hidden fallback.
- Host-supplied stdin is deliberately ignored → verify actual host context delivery as well as direct invocation, retaining the native output envelope.
- Native timeout metadata does not prove every deployment meets a deadline → measure isolated direct runs and distinguish fixed stdin waits from other slow paths.

## Migration Plan

1. Implement and verify the cwd-based dispatcher and CLI together, preserving generated registrations.
2. Update hook documentation and focused compatibility checks. Existing command registrations need no rewrite solely for this change; install the corrected executable through the existing distribution workflow.
3. Verify direct commands with open stdin and, where available, native startup/compaction delivery using disposable settings. Do not alter the user's global hook file during validation.
4. Synchronize current-spec deltas on archive; retain archived historical artifacts.

Rolling back the executable restores the old stdin dependency and can restore the stall. If rollback is necessary, disable the affected advisory registration through its existing management path rather than presenting the old behavior as fixed.

# Tasks

## 1. Bound native callback cadence

- [x] 1.1 Narrow Codex sessionStart to `startup|clear`, narrow Claude sessionStart to `startup|clear|fork`, retain compact restoration, and reject resume payloads; verify focused callback-selection and payload-validation tests pass.
- [x] 1.2 Generate only the two context-delivery registrations per supported agent with five-second timeouts, concise status messages, canonical `pspec resolve hook` commands, and no prompt/tool/stop callbacks; verify native-document tests assert the complete handler shapes.
- [x] 1.3 Update `docs/hook-delivery.md` with the lifecycle allowlist, timeout contract, and explicit absence of per-prompt/tool delivery; verify every documented matcher matches the generated fixtures.

## 2. Contain runtime probe failures

- [x] 2.1 Let condition invocations accept a validated caller-supplied run_json timeout capped by the five-second default, and make hook dispatch use a smaller budget than its native deadline; verify process and condition tests cover default, reduced, invalid, and timeout behavior.
- [x] 2.2 Isolate operational run_json failures to their owning matched trait while keeping authored expression errors atomic, returning diagnostics without losing independent guidance; verify hook tests cover Zmem timeout/exit/JSON failures alongside successful bootstrap and ADHD contributions.
- [x] 2.3 Update `docs/foundation.md` and `docs/hook-delivery.md` to distinguish atomic authored errors from hook-local operational probe failures; verify the documented behavior matches focused dispatch tests.

## 3. Reconcile earlier owned registrations

- [x] 3.1 Reconcile safely owned legacy command aliases and broader resume matchers to the current bounded document through ZuAT while preserving unrelated provider entries and refusing modified/unowned conflicts; verify isolated provisioning tests cover update, reuse, preservation, and conflict cases.
- [x] 3.2 Exercise repeated init/installation reconciliation with the bounded hook asset and verify it produces no duplicate Powerspec callbacks or changes to unrelated native settings.

## 4. Integration verification

- [x] 4.1 Run the focused hook, condition, process, provisioning, and installation test modules with `uv run pytest`, then run the complete required project checks and record any unrelated pre-existing failure separately.
- [x] 4.2 Run `openspec validate bound-runtime-hook-delivery --strict` and verify every modified requirement, scenario, design decision, and completed task remains coherent before implementation is declared complete.

# Tasks

## 1. Cwd-based noninteractive hook resolution

- [x] 1.1 Replace payload input in `src/powerspec/cli/hook.py` and `src/powerspec/hooks.py` with one captured process cwd passed explicitly through dispatch; remove payload-only validation, update all dispatch callers, and verify nearest-consumer discovery, worktree boundaries, runtime condition cwd, and explicit change selection with `uv run pytest tests/test_hooks.py tests/test_repository_investigation.py`.
- [x] 1.2 Add CLI regressions for a stdin sentinel that rejects reads, closed stdin, malformed input, and a payload naming a different repository; verify the actual cwd always wins, unsupported event/agent errors remain on stderr, no-consumer/no-match remains silent, and guidance containing a user question is returned without interaction or state writes.
- [x] 1.3 Replace native payload rejection assertions with registration matcher checks; verify startup/clear, Claude fork, compact routing, resume exclusion, forbidden prompt/tool events, native response envelopes, per-trait exclusions, and optional-probe failure isolation remain correct in the focused hook tests.
- [x] 1.4 Update `docs/hook-delivery.md` and applicable command help to document process-cwd selection, ignored stdin, native matcher ownership, stdout decision guidance, and migration for payload-cwd callers; verify documented direct commands work without piping JSON and no current hook documentation still requires stdin.

## 2. Process and native-host integration evidence

- [x] 2.1 Add real CLI subprocess regressions for sessionStart and afterCompaction on both supported agents with isolated local guidance and an open empty stdin pipe; verify the child exits and emits the expected context before the parent closes stdin, using a bounded wait and guaranteed cleanup of test-owned processes. Run these regressions with `uv run pytest` and record completion timings without external probes.
- [x] 2.2 Verify native startup/compaction context delivery and process cwd with disposable Codex/Claude settings where those hosts are available, preserving the user's global hook configuration; record observed delivery separately from agent adherence, and explicitly report unavailable host checks rather than claiming them passed.
- [x] 2.3 Run the affected CLI/provisioning compatibility tests and `openspec validate remove-hook-stdin-dependency --strict`; verify generated command strings and five-second handler metadata remain compatible and record the completed checks and any remaining limitations before marking the change complete.

## Verification evidence

- Observed red: the stdin sentinel failed at `json.load(sys.stdin)` and the real Codex sessionStart command exceeded a five-second wait while stdin remained open.
- Observed green: the same four real CLI combinations (Codex/Claude, sessionStart/afterCompaction) completed with the input pipe still open in 0.500–0.531 seconds in the first passing run. These isolated cases intentionally contain no external probes.
- `uv run pytest tests/test_hook_input.py tests/test_hooks.py tests/test_repository_investigation.py tests/test_cli.py -q`: 87 passed.
- `uv run pytest tests/test_conditions.py tests/test_provisioning.py tests/test_initialization.py tests/test_skill_cli.py -q`: 61 passed. Strict change validation and `git diff --check` passed.
- Native startup checks on 2026-10-04 used Codex CLI 0.159.1 and Claude Code 2.1.265 with disposable settings and a wrapper recording the actual process cwd before calling the corrected CLI. Both recorded the disposable consumer directory and returned the token supplied only by hook additional context. This demonstrates delivery and recognition of that context, not execution of any referenced skill. Initial smoke attempts failed because of the test wrapper's command quoting; corrected forward-slash executable paths succeeded. User hook settings were not edited.
- Live compaction was not exercised in these one-turn headless smoke sessions; neither host check established a real compact lifecycle transition. Compaction command completion, matcher selection, and native output envelopes are covered by automated tests. This is a remaining native-host validation limitation, not a claim that live compaction passed.
- The global uv tool installation was not replaced. Checks exercised the repository environment; deploying the corrected executable is separate from changing shared hook registrations.

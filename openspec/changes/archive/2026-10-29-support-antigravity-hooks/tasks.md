# Tasks

## 1. Verify the Antigravity hook contract (spike, gates the rest)

- [x] 1.1 On a machine with agy, using a throwaway `HOME`/`USERPROFILE` and a temporary `~/.gemini/config/hooks.json` whose `SessionStart` handler logs its working directory, stdin, and environment variable names to a file, start a new conversation in a project and verify the log shows the cwd is the hooks directory and stdin carries `workspacePaths` as documented; record the result in `design.md` D1-D3
- [x] 1.2 From the same log, check whether the environment already carries the workspace (any documented or observable variable); if it does, stop and amend `design.md` and the specs to use it instead of stdin before continuing, otherwise note that none exists
- [x] 1.3 Make the handler print (a) nothing, (b) `{}`, (c) an `injectSteps` `systemMessage`, and verify a, b are tolerated with exit 0 and c is visible to the model in the conversation; also measure a long message to find any size limit; record in `design.md` D5
- [x] 1.4 Verify whether `SessionStart` fires again when an existing conversation is resumed, and that `pspec` is found on the `PATH` of the spawned hook process; record both and amend the specs if either fails

## 2. Bounded payload reader (portable helper)

- [x] 2.1 Write failing tests in `tests/test_stdin_payload.py` with real pipes: complete object then pipe left open returns immediately; partial then completed object; silent pipe returns `None` within the budget; malformed text; JSON array/string; oversized payload delivered in chunks; terminal stream is not read; verify they fail for the missing module
- [x] 2.2 Implement `read_json_object` in `src/powerspec/utils/` per `design.md` D2 and verify the 2.1 tests pass without using any Powerspec import
- [x] 2.3 Write failing tests, then implement `compose_sections` per `design.md` D3a: intro first, sections in given order, empty sections omitted, a single non-empty section still labeled, empty result when every section is empty; verify with domain-neutral inputs

## 3. Antigravity callback, envelope, and registration

- [x] 3.1 Write failing tests in `tests/test_hooks.py` for: `callback_for("antigravity", "sessionStart")` maps to native `SessionStart` with payload-workspace support; `afterCompaction` raises the no-verified-mapping error; `antigravity:SessionStart` and logical selectors expand correctly and exclude `antigravity` callbacks when a trait excludes them; no high-frequency callback exists
- [x] 3.2 Write failing tests for `serialize("antigravity", ...)`: guidance becomes one `injectSteps[0].systemMessage.systemMessage` with no `hookSpecificOutput`, and no guidance produces no output; and for `native_document("antigravity")`: a single `powerspec` key, a flat `SessionStart` list with one handler of only `type`, `command`, and `timeout` (at most 5), and a command with no quotes or backslashes
- [x] 3.3 Implement the `CALLBACKS` row, `payload_workspace` flag, `serialize`, and `native_document` changes in `src/powerspec/hooks.py` and verify 3.1 and 3.2 pass and the existing Codex and Claude hook tests are unchanged

## 4. Hook command

- [x] 4.1 Write failing CLI tests in `tests/test_hook_input.py`: `--stdin-workspace` with a payload naming a consumer, run from a different cwd, returns that consumer's guidance in the Antigravity envelope; a payload path in a consumer subdirectory finds that consumer; other payload fields do not affect selection; the option is rejected for codex and claude before any read; an unusable payload (empty, malformed, array, no existing directory) writes a stderr diagnostic, prints nothing, exits zero, and does not fall back to the cwd; a malformed config in the only payload workspace exits nonzero with no stdout; interactive stdin uses the cwd
- [x] 4.1a Write failing CLI tests for multi-project payloads using two temporary consumer repositories laid out like a launched workset: one message with the selection instruction and a labeled section per consumer in payload order; two paths in one consumer counted once; one consumer with guidance still labeled; one malformed consumer omitted with a stderr diagnostic and exit zero; every consumer malformed exits nonzero; a missing path skipped; a realistic four-repository result stays under 45,000 characters
- [x] 4.2 Extend `test_real_hook_exits_with_stdin_left_open` with a subprocess that passes a payload and leaves the pipe open, and one that sends nothing, for the new option, and verify both finish within the native five-second limit while the existing Codex and Claude cases still pass without touching stdin
- [x] 4.3 Implement the option in `src/powerspec/cli/hook.py` using the reader and validated callback flag, and verify the 4.1 and 4.2 tests pass and `test_hook_never_touches_stdin` is unchanged

## 5. Provisioning through ZuAT (gated on the Zuat change)

- [x] 5.1 After `add-antigravity-agent` is implemented and a verified Zuat revision exists, bump the `zuat` pin in `pyproject.toml` to it; verify `uv lock` succeeds and `SUPPORTED_AGENTS` includes `antigravity`
- [x] 5.2 Add tests in `tests/test_provisioning.py` and `tests/test_hook_reconciliation.py` against a temporary Antigravity home: first install creates only the `powerspec` entry and keeps other named hooks; repeat reports reused with no write; foreign differing `powerspec` entry fails with diagnostics and is unchanged; stale receipt requires explicit repair; skills install to the unified user directory; verify they pass
- [x] 5.3 Add installation and upgrade tests (`tests/test_installation.py`, `tests/test_upgrading.py`) for `--agent antigravity`, and assert `pspec doctor --agent antigravity` fails as an unsupported agent before any probe; verify they pass

## 6. Documentation

- [x] 6.1 Update `docs/hook-delivery.md`: replace the absolute stdin statement with the default rule plus the explicit `--stdin-workspace` exception, add an Antigravity section (session-start only, no compaction restore, envelope, empty `{}` output, first-workspace rule, unusable-payload behavior), and verify each documented command runs as written
- [x] 6.2 Update `docs/initialization.md` and `README.md` agent lists and examples for `--agent antigravity`, and verify the documented `pspec init --agent antigravity` flow against a throwaway home

## 7. Integration

- [x] 7.1 Run the full `uv run pytest` suite and `openspec validate support-antigravity-hooks --strict`; verify both are green
- [x] 7.2 End to end on a throwaway home: `pspec init --agent antigravity`, start an Antigravity session in a consumer, and verify the guidance appears once at session start and a non-consumer directory receives none; record the observation, noting that delivery is not adherence

## Workflow follow-up

- Every authorized commit follows the zmem commit-authoring skill and requires a passing `pspec check commit` immediately beforehand; active change artifacts stay out of code checkpoints.
- Archive the change after the Zuat change is archived and the pin is verified, then run `pspec state clear --change support-antigravity-hooks`.

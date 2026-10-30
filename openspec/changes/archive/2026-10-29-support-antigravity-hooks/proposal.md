# Proposal

## Why

Once Zuat can manage Antigravity (change `add-antigravity-agent` in the Zuat repository), `pspec init --agent antigravity` will pass agent validation and install skills, but Powerspec's hook delivery will still not work there. Three assumptions built for Codex and Claude break on Antigravity: its `SessionStart` returns context as `injectSteps`, not `hookSpecificOutput`; it has no matcher or compaction event; and it runs a hook with the working directory set to the folder containing `hooks.json` (for user scope, `~/.gemini/config`), so `pspec resolve hook` would find no consumer and silently deliver nothing. The workspace is available only in the hook's stdin payload (`workspacePaths`), which Powerspec currently refuses to read.

## What Changes

- Add an `antigravity` native callback mapping for logical `sessionStart` only, delivered by Antigravity's native `SessionStart`. `afterCompaction` has no native equivalent and stays reported as unsupported for this agent.
- Serialize hook guidance for Antigravity as `{"injectSteps":[{"systemMessage":{"systemMessage":"<guidance>"}}]}`. When there is nothing to deliver, stdout stays empty as for the other agents (verified accepted by Antigravity).
- Register the user-level dispatcher as a keyed `powerspec` entry in Antigravity's `hooks.json` with a flat `SessionStart` handler list, an explicit timeout of at most five seconds, and only handler fields Antigravity documents (no `statusMessage`, no `additionalContextLimit`).
- Add an explicit `--stdin-workspace` option to `pspec resolve hook`, installed only in Antigravity's registration, that reads `workspacePaths` from a bounded, non-blocking stdin read and discovers each listed path's consumer.
- In multi-project sessions (for example an opened Powerspec workset, one worktree per repository), deliver one message with a labeled section per consumer and an instruction to follow only the section for the project the agent is actively implementing or updating changes in. Antigravity lists workspaces alphabetically, so the hook cannot identify the launch directory itself. Codex and Claude behavior, including never touching stdin, is unchanged. **BREAKING** only in that the previous "stdin is never read" statement is no longer absolute; it still holds unless this option is given.
- Keep a direct, interactive `pspec resolve hook sessionStart --agent antigravity` working from the current directory with no payload.
- Update `docs/hook-delivery.md`, `docs/initialization.md`, and the README agent lists, and bump the Zuat pin to the revision containing Antigravity support.

## Capabilities

### New Capabilities
- `antigravity-hook-delivery`: Antigravity's callback mapping, response envelope, keyed registration shape, payload-supplied workspace discovery, and honest limits (no compaction restore, no source filtering).

### Modified Capabilities
- `trait-hook-delivery`: the consumer-discovery requirement admits an opt-in payload workspace for hosts that run hooks from a fixed directory, and the dispatcher-provisioning requirement no longer demands a status message where the host handler has none.
- `cli-product-surface`: the hook command's "reads only its arguments" contract gains the explicit, bounded `--stdin-workspace` exception, and the related resolve-protocol scenarios are scoped accordingly.

## Impact

- `src/powerspec/hooks.py` (callbacks, `serialize`, `native_document`), `src/powerspec/cli/hook.py` (option and bounded payload read), a small portable stdin-reader helper under `src/powerspec/utils/`, and `provisioning.py` only if hook outcome wording needs agent-neutral fixes.
- Tests: `tests/test_hooks.py`, `tests/test_hook_input.py` (extend the open-stdin subprocess test to the new option), `tests/test_provisioning.py`, `tests/test_hook_reconciliation.py`, and installation/upgrade flows against a temporary Antigravity home.
- Dependency: `pyproject.toml` pin of `zuat`. This change cannot be applied until `add-antigravity-agent` is implemented and a verified Zuat revision exists.
- Not covered: `pspec doctor --agent antigravity` (doctor already fails unsupported agents before probes), project-scope Antigravity hooks, and compaction restoration.
- Evidence caveat: Antigravity's hook contract is taken from the agy 1.4.10 bundled guide, not yet from a verified run; the spike in `tasks.md` confirms it before implementation.

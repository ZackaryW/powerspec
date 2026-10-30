# Proposal

## Why

An opened Powerspec workset puts several repositories in one agent session. With `support-antigravity-hooks`, Antigravity sessions receive one labeled guidance section per repository and the agent picks the section for the repository it is implementing or updating changes in. When the agent cannot tell which repository applies (for example a request that names no file, or an OpenSpec action that could belong to several repositories), the behavior is unresolved and the agent has to guess or ask. Real worksets usually have one repository that owns the OpenSpec planning (for example `poc-ab-central` in the 7-repository `poc-ab` workset), so a declared default gives the agent a deterministic fallback.

## What Changes

- Add `pspec workset default <workset> [<label>]` to show, set, or clear (`--clear`) the default member of a saved OpenSpec workset, with `--json`. Setting validates the workset and member through OpenSpec.
- Store defaults in a Powerspec-owned user file, `~/.powerspec/worksets.toml`, never in OpenSpec's registry, which has no such field and which Powerspec must not edit. Each entry keeps the default label, its resolved path, and a snapshot of the workset's member paths.
- `pspec workset launch` carries the source workset's default to the output workset by label, and `pspec workset add` refreshes the stored snapshot after appending a member.
- In a multi-project Antigravity session whose workspace paths exactly match a stored snapshot, the guidance instruction names the default project and tells the agent to use it whenever it cannot determine which project applies; the default's section is marked. The hook reads only the Powerspec file and never calls OpenSpec (about 0.5 s per call, measured).
- No match, a stale snapshot, or an unreadable file means no default: delegation works exactly as without this change.

## Capabilities

### New Capabilities
- `workset-default-project`: declaring, storing, showing, and clearing a workset's default member, and how multi-project guidance names it as the fallback.

### Modified Capabilities
- `workset-launch`: launch carries the default to the output workset, and append refreshes the stored member snapshot.

## Impact

- New `src/powerspec/workset_defaults.py` (file model and matching), a `default` command in `src/powerspec/cli/workset.py`, small hooks in `workset_launch.py` and `worksets.add_source`, and the multi-project composition in `cli/hook.py` from `support-antigravity-hooks`.
- Tests for the command, storage, launch and append carry-over, and hook matching; `docs/worksets.md` and `docs/hook-delivery.md`.
- Depends on `support-antigravity-hooks` (multi-project delivery) being implemented first.
- Codex and Claude are unaffected; they resolve one project from their working directory.

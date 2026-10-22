# Proposal

## Why

Incremental checkpoint guidance currently allows active OpenSpec planning files into commits, and the zmem reminder covers implementation checkpoints rather than every commit. A real Git-index check is needed to detect forbidden paths, including unchanged files already tracked in earlier commits, without confusing instruction delivery with adherence.

## What Changes

- Add a read-only `pspec check commit` command that rejects active OpenSpec change entries anywhere in the proposed repository index and allows canonical archived change paths.
- Keep verified implementation checkpoints incremental while active planning stays local. Require successful spec synchronization and archive before committing change artifacts.
- Require the zmem commit-authoring skill for every authorized commit, including documentation and archive commits, plus the index preflight immediately before committing.
- Verify outcomes with disposable Git repositories, including already tracked active files, force-added ignored files, archives, worktrees and failed checks that preserve state.
- Reconcile this repository's previously tracked active artifacts by removing them from the index while preserving local files, and add ignore rules that retain archive visibility. Do not rewrite history or archive incomplete work.

## Capabilities

### New Capabilities
- `commit-governance`: Incremental commit guidance, archive-only artifact eligibility, and a read-only Git-index preflight.

### Modified Capabilities
None. Existing context publication and hook delivery mechanisms are reused.

## Impact

Adds a CLI group, a small Git index reader and application path policy, focused Git integration tests, shared guidance and checkpoint/archive operation instructions. Updates repository ignore policy and generated OpenSpec configuration. No dependency addition, automatic Git hook installation, commit creation command, zmem runtime replacement, release, push, or history rewrite is introduced. The check establishes index eligibility only; it does not prove spec synchronization, zmem validation, or agent adherence.

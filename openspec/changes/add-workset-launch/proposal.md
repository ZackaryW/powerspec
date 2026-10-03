# Proposal

## Why

OpenSpec worksets collect local folders but do not prepare Git branches or linked worktrees. Powerspec needs a repeatable way to turn a group of advisory source repositories into a separate implementation workspace, with shared branch defaults and per-repository overrides.

## What Changes

- Add `pspec workset add <name> --path <path>` for creating or extending an OpenSpec source workset with validated Git repositories. Appending requires a supported OpenSpec member-update operation.
- Add `pspec workset launch <name> --branch <branch>`, with optional `--name` and unlimited numbered `--repoN`, `--branchN`, `--remoteN`, and `--worktreeN` override groups.
- Launch every source repository. Keep original checkouts available for advisory use and create or reuse standard linked Git worktrees for implementation.
- Default new branches to local `main`, allow explicit remote starting refs, preserve existing branches, and reject incompatible reuse.
- Validate the whole plan before creation. Preserve completed worktrees after partial failure and let retries resume without resetting work.
- Register every store represented in the spawned worktrees as `<original-store-name>-<effective-branch-token>`, including per-repository branch overrides, and update mapped store pointers only inside those worktrees.
- Add `--change <name>` to locate an active change within the source workset and move its complete current contents to its owner's implementation worktree. Add `--store <source-store-id>` for ambiguous names and `--keep-source` to copy instead.
- Verify the destination and finish store/workset registration before removing the source change. Preserve partial results, refuse conflicting destination content, and report cleanup failures without claiming a completed move. Do not create Git commits automatically.
- After every member is ready, create an OpenSpec workset named `<workset-name>-<branch>` or the explicit `--name`, containing only the implementation worktree paths.
- Report the result and an `openspec workset open ...` command. OpenSpec continues to own editor opening.

## Capabilities

### New Capabilities

- `workset-launch`: Source registration, indexed launch options, Git worktree preparation, spawned store registration, change transfer, failure recovery, and publication of the resulting OpenSpec workset.

### Modified Capabilities

None. This adds a command group without changing existing consumer lifecycle requirements.

## Impact

- Add command handlers under `src/powerspec/cli/` and feature-owned orchestration outside the CLI; register the group in `cli/app.py`.
- Reuse Git for repository identity, refs, and worktree operations, and OpenSpec's workset interface for member discovery and final registration. No GitHub API or GitHub Desktop installation is required.
- Add isolated Git integration tests, CLI contract tests, OpenSpec adapter tests, and command documentation.
- Update store identity metadata and recognized configuration pointers in spawned worktrees. Track change-transfer progress locally for retry after source removal; leave original store registrations and unrelated source files intact.
- The installed OpenSpec CLI currently supports create/list/open/remove but cannot append a member. Treat that as an explicit integration constraint rather than replacing OpenSpec's registry or silently deleting and recreating worksets.
- This change is independent of `simplify-implementation-and-deployment`; coordinate only the shared CLI registration file.

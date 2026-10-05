---
name: pspec-workset
description: Prepare multi-repository implementation workspaces with Powerspec worksets. Use when registering Git repositories, launching coordinated worktrees, transferring an active OpenSpec change, or recovering a partial workset launch.
---

# Operate Powerspec worksets

Use `pspec workset` when the user wants separate implementation worktrees for one or more repositories already represented by an OpenSpec workset. OpenSpec owns the saved source and output worksets and editor opening. Powerspec reads that source membership, creates Git worktrees and branch-specific stores, optionally transfers one active change, and publishes the output workset.

Do not treat the source workset or its main-branch checkouts as implementation destinations. Do not edit OpenSpec's private registry, reproduce worktree/store operations manually, or open an editor unless the user asks. Running the command is the operation; this skill does not create a parallel manifest.

## Establish the source workset

Inspect the current saved worksets with `openspec workset list --json` when membership or labels are unclear. Add a repository with:

```text
pspec workset add <name> --path <repository-or-subfolder> --json
```

The path must resolve to a non-bare Git checkout. The repository directory name supplies its default member label. Re-adding the same repository is unchanged. Adding another repository appends it through OpenSpec's remove-and-recreate interface; this is not atomic, so avoid concurrent edits to the same workset and report any recovery instructions returned by the command. Never delete repository folders to repair a failed append.

## Prepare a launch

Use one shared branch for the ordinary case:

```text
pspec workset launch <source> --branch <branch> --json
```

All distinct source repositories launch. New branches start from each repository's local `main`; Powerspec does not fetch. An existing matching branch/worktree is reused, including its commits and local changes.

Use numbered groups only for repositories that differ from the shared defaults:

```text
--repo1 <member-label> --branch1 <branch> --remote1 <remote/ref> --worktree1 <directory-name>
```

Indices may have gaps. Each numbered field belongs to the repository selected by the matching `--repoN`. `--remoteN` chooses an existing local remote-tracking ref and does not authorize a fetch. `--worktreeN` is a safe directory name, not an arbitrary path. Use `--name` only when the default output name `<source>-<shared-branch-token>` is unsuitable.

Before launch, resolve any unclear member label, target branch, base ref, or destination name from repository evidence or the user's explicit choice. Preserve exact branch names in command arguments; Powerspec derives safe directory/store tokens itself.

## Transfer an active change

Append `--change <name>` when the user wants an active OpenSpec change transferred into the launched workspace. Powerspec searches represented source stores. If the name is ambiguous, select the original source store with `--store <id>`.

Change transfer is a move by default: source cleanup occurs only after the destination resolves, spawned stores and pointers are ready, and the output workset is published. Use `--keep-source` only when the user wants a copy. Both `--store` and `--keep-source` require `--change`.

Do not stage, commit, archive, overwrite, or merge transferred files as part of launch. A partially drafted change is eligible. An archived change is not.

## Interpret the result

Prefer `--json` so partial outcomes remain explicit. Treat these fields separately:

- `ok`: the requested operation completed.
- `workspace_ready`: the output workset is usable even if later source cleanup failed.
- `stage` and `errors`: where execution stopped and what needs attention.
- `members` and `effects`: completed actions that must be preserved.
- `stores`: planned source-to-spawned mappings; a listed mapping alone does not prove registration succeeded.
- `transfer`: source, destination, and action, which may still be pending or cleanup-incomplete.
- `opening_command`: the OpenSpec command the user can run to open the completed output workset.

On success, report the output workset, member branches and paths, transferred-change outcome, and opening command. Do not claim the editor was opened.

Worktree directories default to siblings named `<repo>-<branch-token>`. Each spawned store uses `<original-store-id>-<effective-branch-token>`, including per-repository branch overrides. The output workset name uses the shared branch token. Resolve subsequent change work through the spawned store and worktree; keep the original checkout as the source/advisory workspace.

On failure, do not roll back branches, worktrees, stores, pointer edits, copied files, or receipts. Powerspec intentionally preserves completed effects. Correct the reported conflict and retry the same launch command; matching work is reused. For transfer conflicts, compare the retained source, destination, and receipt before changing either side. Do not invent a force, overwrite, or receipt-reset procedure.

If `pspec` or OpenSpec is unavailable, a source workset is missing, or the result cannot establish a safe retry, report the blocker and preserve all observed state rather than replacing the workflow with raw Git commands.

# Worksets

Powerspec uses OpenSpec's saved worksets as input and creates separate implementation worktrees. Git owns branches and checkout metadata; OpenSpec owns membership and editor opening.

```sh
pspec workset add project --path /repos/api
pspec workset launch project --branch feature/payments
pspec workset launch project --branch feature/payments --repo1 api --branch1 feature/backend --remote1 origin/main --worktree1 api-payments
```

All source members launch. Numbered groups override members by their OpenSpec label; positive indices may have gaps. `--repo1=api` is also accepted. Repeated fields, unknown options and conflicting aliases are errors. A subfolder resolves to its Git checkout; aliases of the same Git repository collapse to the first label and position.

New branches start from local `main`, or the explicit local remote-tracking ref supplied by `--remoteN`. Launch never fetches. Existing branches are preserved; a remote override conflicts with an existing branch unless its matching worktree already exists. A matching worktree is reused even after commits or local edits. Source checkouts remain unchanged except for an explicitly requested change move.

The default directory is a sibling of the original checkout: `<repo>-<branch-token>`. Tokens are lowercase, with runs outside ASCII letters, numbers and hyphens replaced by a hyphen and leading/trailing hyphens removed. Empty tokens and conflicting destinations fail. `--worktreeN` supplies a safe single directory name. The output workset is `<source>-<shared-branch-token>`, or `--name <name>`; per-repository branch overrides do not change that name. OpenSpec names must be lowercase kebab-case.

Adding a first repository creates the workset; adding the same repository again is a no-op. To append a different repository, Powerspec reads the saved definition, removes it through `openspec workset remove --yes`, and recreates it with the new member last. Existing member labels, paths, order and preferred tool are preserved. This removes only the saved definition, never the repository folders, branches or worktrees. Powerspec does not edit OpenSpec's private registry.

The remove/create sequence is not atomic. Powerspec rechecks the original definition before removal and verifies the recreated definition. If recreation fails and the name is still free, it attempts to restore the original. If another definition has appeared, it leaves it untouched. Failed or unverifiable recovery reports the original definition for manual recreation; abrupt process termination during the gap can also require manual recovery. Avoid concurrent edits to the same workset during an append.

Successful launch prints `openspec workset open <output> --tool code`. Run that command to open the collection. Powerspec does not launch an editor.

## Stores and changes

Every represented store receives an identity based on its own effective branch: `<original-id>-<branch-token>`. Nested store roots retain their relative locations. The spawned `.openspec-store/store.yaml` changes its `id`, and mapped `store:` fields in spawned OpenSpec configuration point to the spawned IDs. These edits appear in ordinary Git status. Original registrations, source configuration and the global default remain intact. References to stores outside the workset stay unchanged and do not add repositories to the launch. Code-only repositories are not converted to stores.

```sh
pspec workset launch project --branch feature/payments --change add-payments
pspec workset launch project --branch feature/payments --change add-payments --store specifications
pspec workset launch project --branch feature/payments --change add-payments --keep-source
```

`--change` searches active changes only in represented source roots. If several stores contain that name, choose the original ID with `--store`. Both `--store` and `--keep-source` require `--change`. The complete selected directory moves to the same relative path in its owner's worktree; other repositories receive no copies. Uncommitted planning files are included, but unrelated dirty files and temporary consumer state are not. Partially drafted changes are valid; their schema and configuration still need to resolve at the destination. Links, junctions and special files are rejected.

An existing identical destination is reusable. Any byte difference is a conflict, including a committed older proposal. Preflight accounts for Git checkout filters and line endings; the actual copy is checked again before source removal. Powerspec does not overwrite or merge change directories.

Move is the default. Source cleanup happens only after the copied change resolves, all stores/pointers are ready, and the output workset is registered. `--keep-source` selects a copy instead. No Git index is changed, and Powerspec does not commit or archive the change. Tracked source removals remain unstaged deletions.

## Failure and recovery

Use the same launch command to retry. Existing matching worktrees retain commits and local modifications. Publication conflicts never replace a saved member list. Failure can leave created branches/worktrees, store registrations, metadata/pointer edits, or copied files; the result reports its stage and completed effects. No automatic rollback deletes this work.

Transfer progress is kept under the owning destination's Git administrative directory at `powerspec/transfers/`. Receipts are local and uncommitted. A completed move is recognized even after later destination edits. Missing source files alone are not evidence of success. Interrupted cleanup resumes only when the destination and remaining source entries still match the recorded snapshot. New or edited source files are preserved. `workspace_ready: true` with a cleanup failure means the output can be opened but the move is incomplete.

For a conflict, compare the retained source, destination and reported receipt rather than deleting either blindly. Preserve new work separately and restore the expected snapshot before retrying, or finish the transfer manually and stop using that launch as an automatic move. A different transfer mode or output name does not adopt an unrelated receipt. There is no force, overwrite, or receipt-reset option. Concurrent filesystem writers are detected where possible; cleanup is not an atomic cross-directory transaction.

## Output and prerequisites

`--json` returns one object on stdout, including operational failures and partial outcomes. Diagnostics go to stderr. Exit codes are 0 for success, 1 for operational failure, and 2 for invalid arguments. Human output lists branches, paths, created/reused outcomes, changed metadata, mappings, transfer status and the opening command.

Verified with OpenSpec 1.13.2 and Git 2.55.0.windows.5. Git must support `worktree --porcelain -z` and `--attr-source` checkout filtering. On Windows, the npm OpenSpec CLI is invoked through its public JavaScript entrypoint and Node, avoiding batch-shell expansion of path characters. No editor is required to prepare a workset. Appending uses the existing OpenSpec remove/create commands and requires no upstream member-update API.

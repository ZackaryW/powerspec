# Design

## Context

See proposal.md for the motivation and specs/workset-launch/spec.md for observable behavior. This spans CLI parsing, native Git effects, and OpenSpec registration, so a design is needed.

The current Typer application registers command groups in `src/powerspec/cli/app.py`. `presentation.py` already serializes application results. `utils/processes.py` runs literal argv and validates JSON objects, while `utils/inspection.py` supplies bounded executable inspection. `initialization.py` already invokes OpenSpec, but its consumer initialization policy does not belong in workset operations. Current tests cover linked worktree consumer boundaries but no launch orchestration.

The installed OpenSpec workset model contains a name, ordered `{name, path}` members, and an optional preferred tool. `workset list --json` exposes that model; `workset create --member name=path ... --json` registers a new view. `withWorkset` rejects duplicate workset names. There is currently no append/update command, and the internal YAML model is strict. These observations come from installed `dist/core/worksets.js`, `dist/commands/workset.js`, and `dist/commands/workset-input.js`.

## Goals / Non-Goals

**Goals:** Keep Git responsible for repository mechanics and OpenSpec responsible for saved folder collections and editor opening. Make repeat launches inspect actual state, preserve partial progress, and report exactly which stage failed. Allow use from any working directory without initializing a consumer.

**Non-Goals:** Cloning, fetching, merging, copying unrelated dirty source files, installing dependencies into new worktrees, launching editors, managing GitHub Desktop preferences, deleting worktrees, automatically committing, or introducing a separate Powerspec workset registry. Source `main` checkouts are advisory by convention; an explicit change move is the sole source-file removal in this workflow.

## Decisions

### 1. OpenSpec owns source and output collections

`add` creates or appends to the named OpenSpec source workset. `launch` reads that collection and creates a separate output collection after all Git work completes. Use a narrow feature-owned OpenSpec adapter to validate JSON and preserve native errors. Do not import private Node modules or edit its global YAML.

Appending uses a user-selected remove/create sequence through the existing supported CLI. Retain the original definition, recheck it immediately before removal, run `openspec workset remove <name> --yes --json`, and recreate the same name with the added member last and the same preferred tool. Verify the resulting full definition. This does not remove repository folders or perform Git mutations.

On an operation failure, inspect saved state first: an exact intended definition means creation succeeded despite the error; an intact original needs no restoration. If the name is free, attempt to recreate and verify the original definition. Leave any different definition untouched. If recovery fails or cannot be verified, include the original definition in the error for manual recreation. The sequence is not atomic and cannot eliminate races between separate CLI calls or recover automatically from abrupt termination. A Powerspec registry would duplicate membership and is not selected; no upstream changes are required.

### 2. Separate parsing, planning, execution, and publication

Add `cli/workset.py` for input/output and `worksets.py` for feature models and orchestration. An OpenSpec adapter handles collection reads and mutations; generic Git helpers live under `utils/`. Existing presentation helpers emit structured outcomes.

Build an ordered plan containing member aliases, canonical Git identity, source root, target branch, optional starting ref and resolved commit, destination, and intended create/reuse action. Validate all independent facts before mutations, including output name compatibility. Execute repository operations sequentially in source order; recheck relevant facts before each mutation. Inspect actual Git state after any failed or interrupted subprocess and report partial effects. Publish only a complete result.

Use immutable feature-owned result records with `stage`, output workset name, member outcomes, store mappings, optional transfer outcome, errors, and opening command. Git and OpenSpec supply observed state for ordinary launch retries. Change transfer additionally needs a small local receipt because a successful move removes the original discovery path. Creation is not atomic across repositories.

### 3. Unlimited indexed flags remain a small CLI grammar

Keep ordinary Typer options for `--branch`, `--name`, `--json`, `--change`, `--store`, and `--keep-source`. The last two require `--change`; `--store` selects a source store for transfer and does not change the source workset or filter launched repositories. Capture additional launch tokens only for this command and strictly parse `--(repo|branch|remote|worktree)[1-9][0-9]*`, supporting both separated and equals values. Never accept arbitrary unknown kwargs. Reject repeated keys and unresolved selectors. Group numbers associate overrides; source order controls execution. Indices need not be contiguous.

Resolve labels against source membership before deduplicating canonical Git repositories. Multiple aliases cannot prescribe different settings for one repository. No `--repoN` selector changes inclusion. A required shared branch keeps default naming deterministic even when every member is overridden.

Alternative considered: repeatable structured `--repo name=branch` options would fit normal parsing but do not match the requested interface. Restricting the custom parser to indexed fields avoids changing the rest of the CLI.

### 4. Git identity and destination rules

Query Git for checkout root, common Git directory, refs, and worktree registrations. Use the canonical common directory to deduplicate one repository exposed through several members. Source subfolders contribute their owning repository root. Reject bare and unborn repositories. Avoid reusing `find_git_root` as the validator: finding a `.git` marker is not evidence of a valid repository.

Default worktree directories sit beside the original checkout. This adopts GitHub Desktop's ordinary base-directory-plus-name layout while applying the user's `<repo>-<branch>` name convention. It does not read Desktop's private settings or require Desktop. Normalize generated branch tokens as specified, retain the actual Git branch spelling, and reject collisions rather than silently suffixing names. Check resolved parent containment and platform filename restrictions before mutation. Output OpenSpec names use the normalized shared branch token; custom names must meet OpenSpec's naming rules.

Original member order determines output order and its primary member. Duplicate repository aliases collapse to the first label. The output contains worktree roots only, never the advisory paths.

### 5. Ref selection and retry precedence

Check for a matching healthy linked worktree first. Matching identity, expected path, and branch permit reuse, including after commits or dirty edits. An explicit remote starting input does not reset or compare an already reused branch against the old base. This ordering reconciles repeatability with the rule that remote overrides cannot replace existing branches.

If creation is needed, use the existing local branch unchanged when no remote override is supplied. For a new branch, resolve the explicit remote-tracking ref or local `main` to a commit during planning. Use the resolved commit when creating; do not let a changed source HEAD select the base. A branch created concurrently or checked out elsewhere causes an ordinary conflict. Do not pass Git force/reset options. Missing `main` requires an explicit valid remote starting ref; silently inferring `master` or current HEAD is outside this contract.

No network refresh happens during launch. Users explicitly refresh their repositories beforehand. This makes the starting commits inspectable and avoids hidden source mutations.

### 6. Every spawned store gets a branch-specific identity

Discover stores represented by source members through OpenSpec registrations and store identity metadata, retaining the root's relative position within its Git checkout. Deduplicate canonical store roots. Ordinary code repositories are not automatically converted into stores. A pointer to a store outside the source workset does not implicitly add a repository or expand the change search scope.

Build a complete mapping from original store IDs to `<original-id>-<owning-repository-effective-branch-token>` and corresponding spawned roots before mutations. `--name` affects only the output workset. Preflight duplicate generated IDs and IDs registered at other paths. Preserve the original registrations and global default store.

The installed `registerExistingStore` rejects `--id` when it differs from `.openspec-store/store.yaml`. Therefore update only the spawned metadata's `id`, preserving other fields, before invoking supported `openspec store register <spawned-root> --id <new-id> --yes --json`. Read back the registry and verify root/identity health. Missing metadata in the selected branch can be created by OpenSpec registration only for a healthy mapped root; do not initialize unrelated content. Unexpected metadata identities in reused worktrees are conflicts, not permission to rename another store. Track these expected edits as launch effects; they may be visible in Git status.

Rewrite recognized `store:` pointer fields in spawned OpenSpec configuration through ruamel.yaml and the existing atomic file helper. Replace only IDs in the launch mapping; preserve formatting and unrelated values. Pointers already mapped are unchanged on retry. Do not perform text replacement across change documents or rewrite original checkouts. External store pointers remain explicit external dependencies, untouched. Verify effective resolution using OpenSpec: a root with its own planning directories takes precedence over a pointer, so a textual edit alone does not prove routing succeeded. An incompatible or missing spawned root fails before source cleanup.

### 7. Resolve and transfer only the selected change

For `--change`, query the distinct OpenSpec roots represented by source members, using their registered IDs where applicable. Accept only returned roots inside those source repositories; exclude unrelated global defaults from the candidate set. Deduplicate roots reached through multiple members or pointers. A unique active change selects its owner; multiple owners require the original `--store` ID. Archived changes are not eligible. No match or an out-of-workset selector fails preflight. A store owning the change must map to a spawned Git checkout; preserve any nested root-relative path. A repository-local OpenSpec root can transfer to its equivalent worktree root without inventing a source store ID.

Transfer the full selected directory, including `.openspec.yaml` and current uncommitted/untracked planning files. Do not invoke `new change` or regenerate artifacts. Preserve permissions needed by regular files; reject symlinks, reparse-point escapes, and special files rather than following links out of the selected directory. Reject an existing destination that differs from the source; an identical tree can be reused. This includes content inherited by the target branch: launch does not silently replace an older committed proposal with newer local text.

Copy to a private staging directory beside the destination using `shutil`, verify a manifest of relative paths and file hashes, and publish only to an absent destination. Verify an identical existing destination instead of replacing it. Check OpenSpec can resolve the same change and metadata at the mapped root; incomplete planning artifacts may transfer, so do not require implementation readiness. Required schemas/configuration must already be usable in the target; report missing prerequisites without deleting the source.

Before publication of transfer effects, save a versioned local receipt under the owning destination worktree's Git administrative directory in a Powerspec-specific subdirectory. Key it by source workset, output name, source root/change, destination root, and transfer mode. Store the manifest and stage so an interrupted copy or source cleanup can be retried. Use the existing atomic byte writer. The receipt is neither committed nor a second workset registry. Validate all recorded paths against the current launch plan before using it. A missing source plus a matching completed receipt and resolvable destination is an already-completed move; absence of a receipt is not proof that Powerspec moved anything. Preserve later destination edits on completed retries.

After all worktrees, store mappings, destination verification, and output workset registration succeed, remove the source unless `--keep-source` was supplied. Recheck the source manifest and destination immediately before cleanup. Delete only verified snapshot entries; never remove newly appeared or modified files. Stop and report any concurrent edit or cleanup failure; do not claim an atomic directory move. Partial cleanup is recorded so retries can verify remaining files against the original manifest without overwriting the destination. Source removal leaves ordinary unstaged Git deletions for tracked files; do not stage, commit, reset, or archive the change.

### 8. Publication is retryable and opening stays external

Read the intended output workset during preflight. Matching ordered labels and canonical paths mean registration is already satisfied; a mismatch fails. The preferred editor is not part of membership equality and is preserved for an existing output. For a new output, retain the source's preferred tool when compatible. A create-time name race is handled by rereading the saved workset and accepting only a matching member list.

Execution order is: prepare all worktrees; establish spawned store identities and registrations; update and verify mapped pointers; copy and verify the selected change if supplied; register the output workset; finally clean the source for a move. All discoverable conflicts belong in preflight. Recheck at each stage and preserve completed effects on failure. Store registrations or pointer edits can remain after a later failure, and the result must list them for retry.

On success, print paths, branches, created/reused outcomes, store ID mappings, transfer status, the output name, and `openspec workset open <name> --tool code`. Powerspec never invokes that opening command. If registration fails, keep all worktrees and the source change and return the failed publication stage. If final source cleanup fails, report workspace readiness separately from incomplete transfer and exit nonzero. Retrying uses actual state and the transfer receipt. There is no `--open` or editor management subsystem in this change.

### 9. Reusable helper plan

Use native Git via bounded, literal argv subprocess calls. The [Git worktree API](https://git-scm.com/docs/git-worktree) provides creation and machine-readable inventory, and [rev-parse](https://git-scm.com/docs/git-rev-parse) supplies repository/ref discovery. Keep Git responsible for its metadata and locks.

The [GitPython tutorial](https://gitpython.readthedocs.io/en/stable/tutorial.html#using-git-directly) documents `Repo` and direct command access. It is a viable mature interface, but this change needs a small set of installed-Git operations rather than an object database API; adding it would not remove Powerspec's launch planning or OpenSpec integration. Retain the standard library and installed Git. Reuse `run_json_object` for compatible OpenSpec JSON commands and the existing executable inspection helper for prerequisites. Git's NUL-delimited inventory needs byte-preserving subprocess output, so do not force it through a JSON or newline-oriented helper.

Necessary portable helpers under `src/powerspec/utils/git_worktrees.py`:

- `inspect_repository(path: Path, *, timeout: float) -> RepositoryInfo`: discover checkout root, original checkout, common Git directory, and branch/commit facts. Inputs and records contain only Git and filesystem facts. Read-only; missing Git, invalid repositories, and timeout are explicit errors. A release test runner could use the same contract to find an isolated test checkout.
- `list_worktrees(repository: Path, *, timeout: float) -> tuple[WorktreeInfo, ...]`: parse `git worktree list --porcelain -z` into paths, refs, commit IDs, and locked/prunable/detached flags. Preserve unusual paths and inventory order. A developer environment cleanup tool could reuse this inventory without Powerspec.
- `add_worktree(repository: Path, destination: Path, *, branch: str, start_commit: str | None, create_branch: bool, timeout: float) -> WorktreeInfo`: delegate creation to Git, verify the resulting registration, and return observed state. The caller selects branch and base policy. Never reset, overwrite, or roll back; timeout/error can leave partial Git effects which the caller must inspect. A benchmark runner could use this to prepare checkouts for different revisions.

Use native ref validation/resolution directly within this small Git boundary as needed; do not build a general Git framework. Focused tests use disposable repositories, real commits, local remote-tracking refs, paths with spaces, linked worktrees, occupied branches, and observed persistent effects. Application tests separately cover `main` preference, numbered overrides, naming, failure recovery, and OpenSpec publication. Utility implementation and verification precede dependent orchestration.

For transfer, add only portable tree snapshot and verified-copy mechanics under `utils/`: `snapshot_tree(root: Path) -> TreeSnapshot` and `copy_verified_tree(source: Path, destination: Path, snapshot: TreeSnapshot) -> CopyResult`. Use `pathlib`, `hashlib`, `shutil.copytree`, and staging in the destination filesystem. Validate relative containment and reject links/special files, compare the full path/hash manifest, and refuse differing destinations. No helper chooses OpenSpec paths or removes the source. A document export tool can reuse this contract to copy a checked directory without overwriting an existing export. Verify identical reuse, changed source/destination, interrupted staging, nested paths, and escaping links with isolated filesystem tests. Keep removal policy and receipts in the transfer service. Reuse `replace_bytes` for receipts/individual config files and ruamel.yaml for field edits; a generic synchronization package would introduce merge/mirror semantics this transfer does not need.

## Risks / Trade-offs

- OpenSpec lacks an atomic member append -> use the agreed remove/create sequence with a pre-removal recheck, recreation verification and best-effort original-definition restoration. Document the non-atomic gap and preserve concurrent replacement definitions.
- Multi-repository changes cannot be atomic -> preflight, sequential execution, precise partial outcomes, and reuse on retry.
- Concurrent Git operations can invalidate observations -> recheck before effects, let Git enforce locks, and report conflicts rather than forcing operations.
- Name normalization can merge distinct branch spellings -> detect actual destination/workset conflicts; accept explicit names to disambiguate.
- A failed Git command can leave a branch without a complete worktree -> report observed remnants and required manual correction; do not infer ownership or delete them.
- Source `main` and remote-tracking refs can be stale -> show resolved bases; fetching remains an explicit separate user operation.
- Windows command shims and path rules differ -> exercise installed CLI invocation and paths with spaces on Windows as well as isolated Git tests.
- Spawned identity/pointer edits can be committed later -> show them in the launch outcome, retain original registrations, and leave commit/merge decisions to the user.
- Source files can change during cleanup -> compare against the verified snapshot, remove only unchanged entries, preserve conflicts, and record partial cleanup without promising concurrent-writer atomicity.
- A transferred change can outlive its local receipt -> never infer deletion authorization from a missing source or similarly named destination alone.

## Migration Plan

This adds commands and requires no migration of existing consumer profiles. Implement Git and transfer helpers with focused tests, then the OpenSpec adapter and planner, then store mapping, transfer, execution/publication, and CLI integration. Verify append through OpenSpec remove/create, including restoration and conflicts. Validate launches and transfer retries in an isolated OpenSpec data directory, including per-repository store IDs and ambiguous change names. Do not alter the user's saved worksets during verification.

Rolling back Powerspec leaves standard Git worktrees, registered stores, OpenSpec collections, and transferred files intact. A completed move does not automatically return the change to the source. Users retain the verified destination and any cleanup receipt; no automatic deletion or reversal is part of rollback. Coordinate `cli/app.py` with the separate simplification change without making either depend on the other's manifest or packaging changes.

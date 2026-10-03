# Workset Launch Spec Delta

## Purpose

Prepare a group of Git repositories as implementation worktrees and publish their paths as an OpenSpec workset that users can open with their preferred tool.

## ADDED Requirements

### Requirement: Add registers a Git source through OpenSpec

`pspec workset add <name> --path <path>` SHALL validate the given local Git checkout and create or append to the named OpenSpec source workset, using the repository root's directory name as its default member label. Repeated addition of the same repository SHALL be unchanged. An existing label bound to a different repository SHALL produce a conflict. Existing members, order, and preferred opener SHALL be preserved. The operation SHALL NOT create branches, worktrees, or a second Powerspec member registry. To append, Powerspec SHALL retain and recheck the original definition, remove the saved workset through OpenSpec, recreate it with the additional member last, and verify the resulting definition. It SHALL NOT delete member folders or edit OpenSpec's internal registry directly. This sequence SHALL NOT be represented as atomic.

#### Scenario: Create a source workset
- **WHEN** `pspec workset add delivery --path C:\repos\backend` identifies a valid repository and `delivery` does not exist
- **THEN** it creates an OpenSpec workset containing backend's repository root

#### Scenario: Append or repeat a source member
- **WHEN** another repository is added to existing workset `delivery`
- **THEN** it appends that repository while preserving existing members and tool preference, and repeating the same addition is unchanged

#### Scenario: Recreation fails after removal
- **WHEN** appending removes the saved definition but recreation fails and its name is still free
- **THEN** Powerspec attempts to restore and verify the original definition, reports append failure, and supplies the original definition if recovery fails or cannot be verified

#### Scenario: Concurrent definition changes
- **WHEN** the saved definition differs at the pre-removal recheck, or a different definition appears after removal
- **THEN** Powerspec reports the conflict and leaves the observed definition untouched rather than deleting it for recovery

#### Scenario: Creation succeeds despite a lost response
- **WHEN** recreation reports an error but inspection finds the exact intended members and preferred tool
- **THEN** Powerspec reports the append as successful without another removal

### Requirement: Launch uses every source repository

`pspec workset launch <name> --branch <branch>` SHALL read the named OpenSpec workset and prepare every distinct member repository, preserving member order. It SHALL validate membership through Git, including checkouts whose `.git` is a file. Member subfolders SHALL resolve to their containing checkout; multiple members for the same Git repository SHALL produce one implementation worktree using the first member's label. Conflicting overrides through different labels for the same repository SHALL fail. A missing folder, non-Git member, bare repository, or repository without a usable commit SHALL fail validation rather than being silently skipped. Launch SHALL work without requiring a Powerspec consumer in the invoking directory.

#### Scenario: Launch two repositories
- **WHEN** `delivery` contains backend and frontend and the user launches it with branch `payments`
- **THEN** both repositories participate, in source order, even if only frontend has indexed overrides

#### Scenario: Folder and nested OpenSpec member share a repository
- **WHEN** a workset contains a repository root and its `openspec` subfolder
- **THEN** the resulting launch contains one worktree for that repository and does not retain either source folder as an advisory member

#### Scenario: Invalid member
- **WHEN** any source member is unavailable or does not resolve to a supported Git checkout
- **THEN** launch reports the invalid member and creates no branches or worktrees

### Requirement: Indexed options override named members

Launch SHALL accept a required shared `--branch`, optional `--name`, and positive integer indexed groups `--repoN`, `--branchN`, `--remoteN`, and `--worktreeN` without a fixed maximum group count. `--repoN` SHALL identify an existing source member label; each other indexed flag SHALL require its corresponding selector. Overrides SHALL affect that member only and SHALL NOT filter other repositories. Index gaps SHALL be allowed. Unknown options, repeated fields, duplicate repository selectors, missing values, and unknown labels SHALL fail before effects. `--remoteN` SHALL identify a remote-tracking branch such as `origin/main`, not merely a remote name or clone URL.

#### Scenario: Override one branch
- **WHEN** the command is `pspec workset launch delivery --branch payments --repo1 frontend --branch1 payments-ui`
- **THEN** backend uses `payments` and frontend uses `payments-ui`

#### Scenario: Unbounded indexed groups
- **WHEN** valid overrides use indices 1, 12, and 103
- **THEN** the command resolves those groups without requiring intermediate indices

#### Scenario: Malformed group
- **WHEN** the command supplies `--branch2 payments-ui` without `--repo2`
- **THEN** it reports the missing selector before any persistent effect

### Requirement: Source checkouts remain advisory

Launch SHALL preserve source checkout branches, indexes, and unrelated staged, unstaged, and untracked files. An explicitly selected change transfer SHALL be the sole exception: it carries that change's current files and, in move mode, removes only verified source change files at the end. The source repository's `main` branch SHALL be the default starting ref for a new branch, independently of the source checkout's current branch. An explicit `--remoteN` SHALL replace that starting ref. Missing starting refs SHALL fail rather than falling back to an unrelated checkout commit. Launch SHALL use locally available refs and SHALL NOT implicitly fetch, pull, clone, or copy unrelated uncommitted source changes into worktrees.

#### Scenario: Source is dirty and checked out elsewhere
- **WHEN** a source checkout is on `review` with uncommitted changes and its local `main` exists
- **THEN** a new launch branch starts from `main` and the source branch and local changes remain intact

#### Scenario: Explicit remote starting point
- **WHEN** the target branch does not exist and `--remote1 origin/release` resolves locally
- **THEN** the new local target branch starts at that remote-tracking ref's resolved commit

#### Scenario: Starting ref is missing
- **WHEN** a new branch requires `main` or an explicit remote-tracking ref that is absent
- **THEN** preflight reports the missing ref without fetching or substituting HEAD

### Requirement: Standard linked worktrees have predictable destinations

Launch SHALL create standard Git linked worktrees outside the original checkouts. The default destination SHALL be a sibling of the repository's original checkout named `<repo-name>-<branch-token>`. `--worktreeN` SHALL replace the directory name, not the target branch. Generated branch tokens SHALL lowercase names, replace runs outside ASCII lowercase letters, digits, and hyphens with a hyphen, and trim leading and trailing hyphens. Empty tokens and collisions SHALL fail before creation. Explicit worktree names SHALL be single portable directory components: no separators, traversal names, platform-reserved names, invalid filename characters, or trailing dots/spaces. Git branch names themselves SHALL remain unchanged and be validated by Git.

#### Scenario: Branch with a slash
- **WHEN** backend is launched on `feature/payments`
- **THEN** the target branch remains `feature/payments` and the default directory is `backend-feature-payments` beside the original checkout

#### Scenario: Custom worktree name
- **WHEN** frontend has `--branch1 payments-ui --worktree1 frontend-review`
- **THEN** its worktree directory is `frontend-review` and its branch is `payments-ui`

#### Scenario: Unsafe or colliding destination
- **WHEN** a custom name escapes the destination parent or multiple planned paths collide
- **THEN** launch reports the conflict without creating any worktree

### Requirement: Existing branches and worktrees are preserved

An existing target branch SHALL be checked out at its current commit without reset. A healthy linked worktree at the expected path with the expected repository identity and branch SHALL be reused, preserving any new commits and local modifications. An occupied incompatible path, prunable or unusable worktree, or target branch checked out at another path SHALL cause a conflict; launch SHALL NOT force checkout, move, delete, or repair it automatically. An explicit remote starting ref combined with an existing branch SHALL conflict unless a matching worktree is being reused. For matching reuse, the remote option SHALL be treated solely as the original creation input and SHALL NOT reset or retest the branch tip against the starting commit. Original source checkouts SHALL never be reused as implementation members.

#### Scenario: Reuse existing local branch
- **WHEN** the target branch exists, is not checked out elsewhere, and no remote starting override is supplied
- **THEN** a worktree is created at that branch's existing commit

#### Scenario: Repeat launch after implementation
- **WHEN** a matching worktree now contains additional commits and uncommitted changes
- **THEN** launch reuses it without resetting its branch or modifying its files, including when the command repeats its original remote starting override

#### Scenario: Remote override conflicts with existing branch
- **WHEN** a branch already exists, no matching worktree exists, and a remote starting override is supplied
- **THEN** launch reports a conflict instead of resetting the branch

#### Scenario: Branch occupied elsewhere
- **WHEN** the target branch is already checked out at an unexpected path or in the original checkout
- **THEN** launch reports the occupied branch and preserves the checkout

### Requirement: Preflight and retries preserve partial progress

Launch SHALL validate options, prerequisites, every repository/ref/destination, store identity mappings, selected change ownership, and output workset compatibility before creating branches or worktrees. It SHALL report all independently discoverable preflight conflicts together. It SHALL recheck mutation-sensitive facts when applying the plan and stop on an execution failure. Successful worktrees, store registrations, pointer edits, transferred files, and any Git effects left by a failed operation SHALL be preserved and reported. A later invocation SHALL inspect actual state and reuse matching completed effects. Launch SHALL NOT publish a new output workset while any member, store routing, or requested destination change verification is incomplete. Final source cleanup SHALL follow publication. Launch SHALL NOT claim cross-repository atomicity or perform automatic rollback.

#### Scenario: Preflight finds multiple conflicts
- **WHEN** one repository lacks its starting ref and another has an occupied destination
- **THEN** both conflicts are reported and neither repository is changed

#### Scenario: Second creation fails
- **WHEN** backend's worktree succeeds and frontend fails during creation
- **THEN** backend is preserved, frontend's observed result and remaining work are reported, and the output workset is not registered

#### Scenario: Retry partial launch
- **WHEN** the same command is repeated after the frontend problem is corrected
- **THEN** backend's matching worktree is reused and the missing frontend worktree is prepared

### Requirement: Complete launches publish an OpenSpec workset

After every member, spawned store registration, mapped pointer, and requested destination change is ready, Powerspec SHALL create an OpenSpec workset named `<source-workset-name>-<branch-token>` unless `--name` supplies a valid OpenSpec name. The shared branch SHALL determine the default workset name regardless of per-repository branch overrides. The output SHALL contain only implementation worktree roots with their retained labels and order. The source workset membership SHALL remain unchanged. A matching existing output workset SHALL be treated as already registered; a differing member list or a name equal to the source name SHALL conflict without overwrite. Registration failure SHALL preserve all prepared worktrees and the selected source change, report failure, and permit registration to be retried. Powerspec SHALL use OpenSpec's supported interface for registry mutations.

#### Scenario: Publish implementation paths
- **WHEN** `delivery` is fully launched with shared branch `payments` and frontend override `payments-ui`
- **THEN** `delivery-payments` contains only the backend and frontend implementation worktrees and `delivery` retains its original members

#### Scenario: Custom launch name
- **WHEN** the command supplies `--name payments-work`
- **THEN** the output OpenSpec workset is named `payments-work`

#### Scenario: Existing output conflicts
- **WHEN** the desired output name already contains different member paths
- **THEN** preflight fails without overwriting the saved workset or creating worktrees

#### Scenario: Registration fails after preparation
- **WHEN** every worktree is ready but OpenSpec registration fails
- **THEN** the command reports registration failure, preserves the worktrees, and can reuse them on retry

### Requirement: Opening stays with OpenSpec

Workset commands SHALL report concise human-readable outcomes by default and support `--json`. Launch success SHALL identify the output workset, each repository's path and branch and whether it was created or reused, spawned store ID mappings, requested change-transfer status, and a ready-to-run `openspec workset open <output-name> --tool code` command. Powerspec SHALL NOT launch an editor itself. JSON mode SHALL emit one result object on stdout, including partial outcomes on operational failure, while diagnostics go to stderr. Usage errors SHALL exit 2, operational failures 1, and success 0. Reading help SHALL cause no persistent effects.

#### Scenario: Successful handoff
- **WHEN** launch successfully prepares and registers `delivery-payments`
- **THEN** it prints the workset name and the OpenSpec opening command without spawning VS Code

#### Scenario: Structured partial failure
- **WHEN** JSON launch fails after one successful worktree
- **THEN** stdout contains one failure result with that completed worktree and the failing stage, stderr contains the diagnostic, and the exit code is 1

### Requirement: Spawned stores use their owning branch in their identity

Every store represented in a launched source repository SHALL receive a registration for its corresponding spawned root named `<original-store-name>-<effective-branch-token>`, even when `--change` is absent. The token SHALL use the owning repository's effective branch and the existing branch-token normalization rule. Custom workset names SHALL NOT change store IDs. The spawned identity metadata SHALL match its new registered ID while preserving unrelated metadata. Original store identities, registrations, and global default selection SHALL remain unchanged. Existing generated IDs at the expected root SHALL be reused; IDs bound to other roots, conflicting identities, or multiple stores generating the same ID SHALL fail without replacing registrations. Ordinary code roots SHALL NOT become stores merely because they are workset members.

#### Scenario: Register every store without change transfer
- **WHEN** a workset contains stores `specifications` and `contracts`, launched on `payments` without `--change`
- **THEN** their spawned roots register as `specifications-payments` and `contracts-payments`, and the original registrations are preserved

#### Scenario: Per-repository branch determines store ID
- **WHEN** specifications uses branch override `feature/api` and the output workset has custom name `review`
- **THEN** its spawned store ID is `specifications-feature-api`, independent of `review`

#### Scenario: Store registration collision
- **WHEN** `specifications-payments` is registered at a different directory
- **THEN** preflight reports the conflict without repointing it or unregistering the source store

### Requirement: Spawned pointers resolve mapped stores

Launch SHALL rewrite recognized OpenSpec store-pointer fields inside spawned worktrees from original IDs to their mapped spawned IDs, preserving unrelated configuration. It SHALL leave original checkout configuration and references to stores outside the launch mapping unchanged. It SHALL verify effective OpenSpec resolution at each rewritten consumer; a successful text edit alone SHALL NOT count as successful routing. A reused worktree with an unexpected conflicting pointer or store identity SHALL produce a conflict rather than having user changes overwritten. Launch SHALL NOT expand membership to include external stores automatically.

#### Scenario: Code worktree follows its specification worktree
- **WHEN** backend's source configuration points to `specifications` and that store is spawned on `payments`
- **THEN** backend's spawned configuration points to `specifications-payments`, OpenSpec resolves that spawned root, and the source configuration still points to `specifications`

#### Scenario: External store pointer
- **WHEN** a worktree references a store outside the source workset
- **THEN** the pointer remains unchanged and that store is neither spawned nor searched implicitly for the selected change

### Requirement: Change selection is bounded to source workset owners

`--change <name>` SHALL resolve an active change among distinct OpenSpec roots represented by the source workset. Multiple members reaching the same root SHALL count as one owner. A unique match SHALL select that owner automatically; distinct matching owners SHALL require `--store <original-store-id>` and report the candidates. The selector SHALL refer to a store in the source workset and SHALL NOT change repository inclusion. No match, an archived-only match, an out-of-workset selector, or an owner without a corresponding launched checkout SHALL fail before effects. `--store` and `--keep-source` SHALL require `--change`. Global default stores outside the workset SHALL NOT participate in discovery.

#### Scenario: Find a unique owner
- **WHEN** only `specifications` contains active change `add-payments` within `delivery`
- **THEN** `--change add-payments` selects that root and maps it to the specifications worktree

#### Scenario: Disambiguate a change
- **WHEN** two source stores contain `add-payments` and the command supplies `--store specifications`
- **THEN** only that store's change is selected while every source repository still launches

#### Scenario: Ambiguous or external owner
- **WHEN** multiple distinct roots match without a selector, or the supplied selector is outside the workset
- **THEN** launch reports an ownership error and performs no mutations

### Requirement: Change transfer preserves the complete selected directory

Change transfer SHALL target the same relative change path within its owner's spawned OpenSpec root, without distributing copies to other repositories. It SHALL preserve the complete current directory, including metadata, nested artifacts, and uncommitted or untracked planning files. It SHALL NOT copy unrelated source files or temporal consumer state. An identical existing destination SHALL be reusable; differing destination content SHALL cause a conflict without overwrite. Links or special files that cannot be safely copied within the selected boundary SHALL be rejected. The copied tree SHALL be verified against its source snapshot and the change SHALL resolve through OpenSpec at the destination. Incomplete planning artifacts SHALL not by themselves prevent transfer. Missing required configuration or schema resources SHALL be reported before source removal.

#### Scenario: Transfer uncommitted planning files
- **WHEN** the selected change includes `.openspec.yaml`, a modified proposal, and an untracked supplementary document and its target is absent
- **THEN** all selected change files arrive with verified contents in the owner's implementation root and unrelated source files remain untouched

#### Scenario: Different inherited destination
- **WHEN** the target branch already contains a different version of the selected change
- **THEN** launch reports the conflicting destination without overwriting it or deleting the source

#### Scenario: Partially drafted change
- **WHEN** an active change has valid metadata and a proposal but no tasks yet
- **THEN** it can transfer without creating missing artifacts or claiming implementation readiness

### Requirement: Moving cleans the source only after successful handoff

`--change` SHALL move by default; `--keep-source` SHALL copy and retain the source. In move mode, source cleanup SHALL begin only after all worktrees, store registrations, mapped pointers, verified destination content, and output workset registration succeed. Source entries SHALL be rechecked against the transferred snapshot and only unchanged verified entries SHALL be removed. Concurrent additions or edits SHALL be preserved and reported as incomplete cleanup. Failure SHALL preserve the destination and report workspace readiness separately from transfer completion with a nonzero exit status. Tracked source removals SHALL remain ordinary Git working-tree deletions; Powerspec SHALL NOT stage, commit, or archive them automatically.

#### Scenario: Default move completes
- **WHEN** transfer verification and all registrations succeed and source content remains unchanged
- **THEN** the selected source change directory is removed, its verified destination remains active, and tracked deletions are left for the user to commit

#### Scenario: Keep-source alternative
- **WHEN** launch supplies `--change add-payments --keep-source`
- **THEN** the destination is verified and registered and the source change remains present

#### Scenario: Source changes or removal fails
- **WHEN** source content changes after copying or removal encounters an error
- **THEN** the destination is preserved and the command reports workspace readiness and incomplete source cleanup without claiming the move succeeded

#### Scenario: Registration failure prevents cleanup
- **WHEN** copying succeeds but store or output workset registration has not succeeded
- **THEN** the source is retained and all completed effects are reported for retry

### Requirement: Transfer retries distinguish completed moves from missing changes

Transfer SHALL retain local, uncommitted progress evidence identifying the selected source, mapped destination, snapshot, transfer mode, and completed stages. Retries SHALL validate that evidence against the requested launch and observed state. A missing source alone SHALL NOT establish a completed move. A matching completed transfer with a resolvable destination SHALL be recognized without overwriting later implementation edits. Partial cleanup SHALL resume only for remaining source entries that still match the verified snapshot and after destination content is verified; unexpected content SHALL remain untouched.

#### Scenario: Repeat after completed move
- **WHEN** the source change is absent, a matching completion receipt exists, and implementation has updated the destination
- **THEN** launch reports the transfer already completed and preserves the implementation edits

#### Scenario: Missing source without evidence
- **WHEN** no source change is found and no matching completed transfer evidence exists
- **THEN** launch reports the missing change instead of inferring success from a similarly named destination

#### Scenario: Resume interrupted cleanup
- **WHEN** progress records verified transfer but only some source files were removed
- **THEN** a retry verifies the destination and remaining original files before resuming cleanup, preserving any new or changed source files

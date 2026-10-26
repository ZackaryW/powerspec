# Workset Launch Specification

## Purpose

Prepare a group of Git repositories as implementation worktrees and publish their paths as an OpenSpec workset that users can open with their preferred tool.

## Requirements

### Requirement: Add registers a Git source through OpenSpec

`pspec workset add <name> --path <path>` SHALL validate the local Git checkout and create or append to the named OpenSpec source workset, labelling the member by its repository root's directory name by default. A repeated addition SHALL leave it unchanged, a label bound to another repository SHALL conflict, and existing members, order and opener SHALL be preserved. The operation SHALL NOT create branches, worktrees or a second Powerspec member registry.

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

`pspec workset launch <name> --branch <branch>` SHALL prepare every distinct member repository of the named workset in order, validating membership via Git, including `.git` files. Member subfolders SHALL resolve to their checkout, and members sharing a repository SHALL yield one worktree under the first label; conflicting overrides via different labels SHALL fail. Missing, non-Git, bare or commitless members SHALL fail, not be skipped. No consumer SHALL be required in the invoking directory.

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

Launch SHALL accept a required shared `--branch`, optional `--name`, and unbounded positive indexed groups `--repoN`, `--branchN`, `--remoteN` and `--worktreeN`, where `--repoN` names an existing member label and each other flag requires its selector. Overrides SHALL affect only that member without filtering others, and index gaps SHALL be allowed. Unknown options, repeated fields, duplicate selectors, missing values and unknown labels SHALL fail before effects.

#### Scenario: Override one branch
- **WHEN** the command is `pspec workset launch delivery --branch payments --repo1 frontend --branch1 payments-ui`
- **THEN** backend uses `payments` and frontend uses `payments-ui`

#### Scenario: Unbounded indexed groups
- **WHEN** valid overrides use indices 1, 12, and 103
- **THEN** the command resolves those groups without requiring intermediate indices

#### Scenario: Malformed group
- **WHEN** the command supplies `--branch2 payments-ui` without `--repo2`
- **THEN** it reports the missing selector before any persistent effect

#### Scenario: Remote option needs a tracking branch
- **WHEN** `--remoteN` is given only a remote name or a clone URL
- **THEN** launch fails before effects because it requires a remote-tracking branch such as `origin/main`

### Requirement: Source checkouts remain advisory

Launch SHALL preserve source checkout branches, indexes and unrelated staged, unstaged and untracked files. Only an explicitly selected change transfer SHALL carry its files and, when moving, remove verified source change files at the end. A new branch SHALL start from the source repository's `main` unless `--remoteN` replaces it, and a missing starting ref SHALL fail without fallback. Launch SHALL use local refs, never fetching, pulling, cloning or copying unrelated uncommitted changes.

#### Scenario: Source is dirty and checked out elsewhere
- **WHEN** a source checkout is on `review` with uncommitted changes and its local `main` exists
- **THEN** a new launch branch starts from `main` and the source branch and local changes remain intact

#### Scenario: Explicit remote starting point
- **WHEN** the target branch does not exist and `--remote1 origin/release` resolves locally
- **THEN** the new local target branch starts at that remote-tracking ref's resolved commit

#### Scenario: Starting ref is missing
- **WHEN** a new branch requires `main` or an explicit remote-tracking ref that is absent
- **THEN** preflight reports the missing ref without fetching or substituting HEAD

#### Scenario: Source on another branch still starts from main
- **WHEN** the source checkout has a feature branch checked out and no `--remoteN` is given
- **THEN** the new branch starts from the source repository's `main`

### Requirement: Standard linked worktrees have predictable destinations

Launch SHALL create standard Git linked worktrees outside the originals, by default as a sibling named `<repo-name>-<branch-token>`, where `--worktreeN` replaces the directory name, not the branch. Branch tokens SHALL be lowercase, with runs outside `[a-z0-9-]` made one hyphen and edge hyphens trimmed; empty tokens and collisions SHALL fail before creation. Explicit worktree names SHALL be single portable directory components, and Git branch names SHALL stay unchanged and be validated by Git.

#### Scenario: Branch with a slash
- **WHEN** backend is launched on `feature/payments`
- **THEN** the target branch remains `feature/payments` and the default directory is `backend-feature-payments` beside the original checkout

#### Scenario: Custom worktree name
- **WHEN** frontend has `--branch1 payments-ui --worktree1 frontend-review`
- **THEN** its worktree directory is `frontend-review` and its branch is `payments-ui`

#### Scenario: Unsafe or colliding destination
- **WHEN** a custom name escapes the destination parent or multiple planned paths collide
- **THEN** launch reports the conflict without creating any worktree

#### Scenario: Non-portable worktree name
- **WHEN** `--worktreeN` contains a separator, traversal name, platform-reserved name, invalid filename character, or trailing dot or space
- **THEN** launch fails before creating anything

### Requirement: Existing branches and worktrees are preserved

An existing target branch SHALL be checked out at its current commit without reset, and a healthy linked worktree at the expected path with the expected repository and branch SHALL be reused with its commits and changes. Incompatible occupied paths, prunable or unusable worktrees, or a branch checked out elsewhere SHALL conflict without forced checkout, move, deletion or repair. Original source checkouts SHALL never be reused as implementation members.

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

#### Scenario: Reuse ignores the remote starting point
- **WHEN** a matching worktree is reused while `--remoteN` was given
- **THEN** the remote is treated only as the original creation input and the branch tip is neither reset nor compared with it

### Requirement: Preflight and retries preserve partial progress

Launch SHALL validate options, prerequisites, every repository, ref and destination, store mappings, change ownership and output compatibility before creating branches or worktrees, reporting all discoverable conflicts together. It SHALL recheck mutation-sensitive facts while applying and stop on an execution failure. Completed worktrees, registrations, pointer edits, transferred files and leftover Git effects SHALL be kept and reported, and later runs SHALL reuse matching effects.

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

Once every member, spawned store, mapped pointer and requested change is ready, Powerspec SHALL create an OpenSpec workset named `<source-workset-name>-<branch-token>` from the shared branch, or a valid `--name`, holding only implementation roots with their labels and order, leaving the source workset unchanged. A matching existing output SHALL count as registered; differing members or the source's name SHALL conflict without overwrite. Registry changes SHALL use OpenSpec's supported interface.

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

Workset commands SHALL report concise human outcomes by default and support `--json`. Launch success SHALL report the output workset, each repository's path, branch and created/reused status, store mappings, transfer status and a ready `openspec workset open <output-name> --tool code` command, without opening an editor. JSON mode SHALL emit one stdout object, including partial outcomes, with diagnostics on stderr. Exit codes SHALL be 2 for usage errors, 1 for operational failure, 0 for success.

#### Scenario: Successful handoff
- **WHEN** launch successfully prepares and registers `delivery-payments`
- **THEN** it prints the workset name and the OpenSpec opening command without spawning VS Code

#### Scenario: Structured partial failure
- **WHEN** JSON launch fails after one successful worktree
- **THEN** stdout contains one failure result with that completed worktree and the failing stage, stderr contains the diagnostic, and the exit code is 1

#### Scenario: Help has no effects
- **WHEN** a user reads workset command help
- **THEN** nothing persistent changes

### Requirement: Spawned stores use their owning branch in their identity

Each store in a launched repository SHALL be registered for its spawned root as `<original-store-name>-<effective-branch-token>`, even without `--change`, using its repository's effective branch and the token rule; custom workset names SHALL NOT change store IDs. Spawned identity metadata SHALL match the new ID, keeping unrelated metadata, and original identities, registrations and the global default SHALL stay unchanged. Ordinary code roots SHALL NOT become stores merely as members.

#### Scenario: Register every store without change transfer
- **WHEN** a workset contains stores `specifications` and `contracts`, launched on `payments` without `--change`
- **THEN** their spawned roots register as `specifications-payments` and `contracts-payments`, and the original registrations are preserved

#### Scenario: Per-repository branch determines store ID
- **WHEN** specifications uses branch override `feature/api` and the output workset has custom name `review`
- **THEN** its spawned store ID is `specifications-feature-api`, independent of `review`

#### Scenario: Store registration collision
- **WHEN** `specifications-payments` is registered at a different directory
- **THEN** preflight reports the conflict without repointing it or unregistering the source store

#### Scenario: Existing generated ID is reused
- **WHEN** the expected spawned store ID is already registered at the expected root
- **THEN** launch reuses that registration instead of replacing it

### Requirement: Spawned pointers resolve mapped stores

Launch SHALL rewrite recognized OpenSpec store-pointer fields in spawned worktrees from original to mapped spawned IDs, keeping unrelated configuration, original checkouts and references outside the mapping. It SHALL verify effective OpenSpec resolution at each rewritten consumer, and a text edit alone SHALL NOT count as routing. A reused worktree with a conflicting pointer or store identity SHALL conflict rather than be overwritten, and launch SHALL NOT add external stores to membership.

#### Scenario: Code worktree follows its specification worktree
- **WHEN** backend's source configuration points to `specifications` and that store is spawned on `payments`
- **THEN** backend's spawned configuration points to `specifications-payments`, OpenSpec resolves that spawned root, and the source configuration still points to `specifications`

#### Scenario: External store pointer
- **WHEN** a worktree references a store outside the source workset
- **THEN** the pointer remains unchanged and that store is neither spawned nor searched implicitly for the selected change

### Requirement: Change selection is bounded to source workset owners

`--change <name>` SHALL resolve an active change among distinct OpenSpec roots in the source workset, counting members that reach one root once. A unique match SHALL select its owner; distinct matches SHALL require `--store <original-store-id>` and report candidates, without changing repository inclusion. No match, archived-only matches, an out-of-workset selector, or an owner without a launched checkout SHALL fail before effects. `--store` and `--keep-source` SHALL require `--change`.

#### Scenario: Find a unique owner
- **WHEN** only `specifications` contains active change `add-payments` within `delivery`
- **THEN** `--change add-payments` selects that root and maps it to the specifications worktree

#### Scenario: Disambiguate a change
- **WHEN** two source stores contain `add-payments` and the command supplies `--store specifications`
- **THEN** only that store's change is selected while every source repository still launches

#### Scenario: Ambiguous or external owner
- **WHEN** multiple distinct roots match without a selector, or the supplied selector is outside the workset
- **THEN** launch reports an ownership error and performs no mutations

#### Scenario: Global default store is ignored
- **WHEN** a global default store outside the source workset contains a matching change
- **THEN** it does not participate in change discovery

### Requirement: Change transfer preserves the complete selected directory

Change transfer SHALL target the same relative change path in its owner's spawned OpenSpec root only, copying the complete current directory, including metadata, nested artifacts and uncommitted or untracked planning files, but no unrelated files or temporal state. An identical destination SHALL be reused; differing content SHALL conflict without overwrite. Unsafe links or special files SHALL be rejected. The copy SHALL match its source snapshot and resolve through OpenSpec at the destination.

#### Scenario: Transfer uncommitted planning files
- **WHEN** the selected change includes `.openspec.yaml`, a modified proposal, and an untracked supplementary document and its target is absent
- **THEN** all selected change files arrive with verified contents in the owner's implementation root and unrelated source files remain untouched

#### Scenario: Different inherited destination
- **WHEN** the target branch already contains a different version of the selected change
- **THEN** launch reports the conflicting destination without overwriting it or deleting the source

#### Scenario: Partially drafted change
- **WHEN** an active change has valid metadata and a proposal but no tasks yet
- **THEN** it can transfer without creating missing artifacts or claiming implementation readiness

#### Scenario: Missing configuration is reported before removal
- **WHEN** the destination lacks required OpenSpec configuration or schema resources
- **THEN** transfer reports it before any source removal

### Requirement: Moving cleans the source only after successful handoff

`--change` SHALL move by default, and `--keep-source` SHALL copy and keep the source. In move mode, cleanup SHALL begin only after worktrees, store registrations, mapped pointers, verified destination content and output workset registration succeed, and SHALL remove only entries still matching the transferred snapshot, preserving and reporting concurrent edits. Failure SHALL keep the destination and exit nonzero, reporting workspace readiness separately from transfer completion.

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

#### Scenario: Removals are left unstaged
- **WHEN** move mode removes tracked source change files
- **THEN** they remain ordinary working-tree deletions that Powerspec does not stage, commit or archive

### Requirement: Transfer retries distinguish completed moves from missing changes

Transfer SHALL keep local, uncommitted progress evidence naming source, mapped destination, snapshot, mode and completed stages, and retries SHALL validate it against the requested launch and observed state. A missing source alone SHALL NOT establish a completed move. A matching completed transfer with a resolvable destination SHALL be recognized without overwriting later edits, and partial cleanup SHALL resume only for entries still matching the verified snapshot after destination verification.

#### Scenario: Repeat after completed move
- **WHEN** the source change is absent, a matching completion receipt exists, and implementation has updated the destination
- **THEN** launch reports the transfer already completed and preserves the implementation edits

#### Scenario: Missing source without evidence
- **WHEN** no source change is found and no matching completed transfer evidence exists
- **THEN** launch reports the missing change instead of inferring success from a similarly named destination

#### Scenario: Resume interrupted cleanup
- **WHEN** progress records verified transfer but only some source files were removed
- **THEN** a retry verifies the destination and remaining original files before resuming cleanup, preserving any new or changed source files

#### Scenario: Receipt destination approaches the host path limit
- **WHEN** an otherwise valid launch needs a long receipt filename near the host path limit and the host supports both that destination and short temporary files in its parent directory
- **THEN** transfer records its progress and completes normally without relocating repositories or enabling a different operating-system path policy
- **AND** a repeated launch recognizes its receipt at the same location and preserves later destination edits

#### Scenario: Receipt publication fails before transfer
- **WHEN** a launch has prepared worktrees but cannot publish its initial transfer progress evidence
- **THEN** it reports the transfer failure, preserves the selected source and completed worktrees, and does not publish an incomplete output workset
- **AND** after the publication problem is corrected, a retry reuses matching worktrees and completes the requested transfer

#### Scenario: Receipt identities stay compatible
- **WHEN** a retry finds progress evidence written by an earlier Powerspec version
- **THEN** its existing receipt identity and location are still recognized

### Requirement: Appending recreates the workset through OpenSpec

To append a member, Powerspec SHALL keep and recheck the original definition, remove the saved workset through OpenSpec, recreate it with the new member last, and verify the result. It SHALL NOT delete member folders or edit OpenSpec's internal registry directly, and SHALL NOT present this sequence as atomic.

#### Scenario: Append verifies the recreated definition
- **WHEN** a member is appended to an existing workset
- **THEN** the recreated definition is compared with the intended members before success is reported

#### Scenario: Member folders are untouched
- **WHEN** the saved workset is removed during an append
- **THEN** no member folder is deleted and OpenSpec's registry is changed only through OpenSpec

### Requirement: Launch publishes only after full verification

Launch SHALL NOT publish a new output workset while any member, store routing or requested destination change verification is incomplete, and final source cleanup SHALL follow publication. Launch SHALL NOT claim cross-repository atomicity or perform automatic rollback.

#### Scenario: Incomplete verification blocks publication
- **WHEN** one member's store routing cannot be verified
- **THEN** no output workset is published

#### Scenario: No automatic rollback
- **WHEN** a launch fails after some worktrees were created
- **THEN** those effects remain and are reported rather than rolled back

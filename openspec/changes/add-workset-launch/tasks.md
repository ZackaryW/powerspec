# Tasks

## 1. Portable Git mechanics

- [x] 1.1 Implement repository identity and NUL-delimited worktree inspection under `src/powerspec/utils/` with documented portable contracts; verify using real disposable normal and linked checkouts, subfolders, paths with spaces, detached/prunable entries, and invalid repositories through focused `uv run pytest` tests.
- [x] 1.2 Implement bounded native Git worktree creation and ref validation/resolution without reset or force behavior; verify new and existing branches, exact starting commits, occupied branches, source preservation, timeout/error reporting, and post-operation inventory through real Git fixtures.
- [x] 1.3 Implement portable tree snapshots and verified copy under `utils/`, documenting the ordinary path/hash contract; verify nested and untracked files, identical reuse, differing destinations, source edits during copy, interrupted staging, and link/reparse-point rejection with isolated filesystem tests.

## 2. OpenSpec workset adapter and source registration

- [x] 2.1 Add a feature-owned adapter for OpenSpec JSON listing and creation using existing process/presentation mechanics where suitable; verify malformed output, missing prerequisites, Windows executable invocation, preserved member order/tool, duplicate-name races, and isolated registry creation.
- [x] 2.2 Implement source repository validation, new-workset creation and repeated-add no-op behavior; verify invalid inputs and duplicate labels leave source worksets untouched.
- [x] 2.3 Append through the user-selected OpenSpec remove/create sequence; preserve existing members/order/tool, recheck the original before removal, verify recreation, restore the original on failure when the name is free, and preserve concurrent replacements. Verify failure/recovery paths and real installed CLI append. Document the non-atomic gap and manual recovery evidence without editing OpenSpec's private registry.
- [x] 2.4 Extend the adapter to discover represented stores, register spawned roots through OpenSpec, and inspect effective change/root resolution; verify metadata-ID mismatches, repeated same-root registration, conflicting IDs, and exclusion of unrelated global defaults using an isolated OpenSpec registry.

## 3. Launch planning and validation

- [x] 3.1 Implement feature models and strict indexed override parsing, including separated/equals forms and arbitrarily large positive indices; verify default/override precedence, gaps, missing selectors, duplicate fields, unknown flags, and alias conflicts through focused parser and CLI-entrypoint tests.
- [x] 3.2 Build ordered launch plans from all source members with canonical repository deduplication, branch/base selection, matching-worktree reuse, destination/name validation, and output-workset compatibility; verify aggregate preflight errors cause zero effects, including missing main/remote refs, unsafe paths, occupied branches, and normalization collisions.
- [x] 3.3 Document launch examples, exact naming/default rules, no implicit fetch, and existing-branch/remote-override behavior alongside the planner; verify examples against fixtures with a dirty advisory checkout and a repository shared by multiple source member paths.
- [x] 3.4 Plan every represented store's original-ID to effective-branch-ID/root mapping and resolve optional change ownership; verify per-repository overrides, custom workset names, duplicate owner aliases, ambiguous names, `--store` selection, absent/archived changes, and out-of-workset owners before any effects.

## 4. Worktree execution and store routing

- [x] 4.1 Execute validated plans sequentially with mutation-sensitive rechecks and truthful partial outcomes; verify injected second-repository failures, concurrent branch creation, and retry after commits/local edits preserve all prior work, including reuse with a repeated remote override.
- [x] 4.2 Prepare spawned identity metadata, register all spawned stores, and rewrite only mapped store-pointer fields with existing YAML/atomic helpers; verify actual OpenSpec routing, preserved original IDs/configuration/global defaults, unchanged external pointers, collision failures, and repeat-run preservation of unexpected user edits. Document visible metadata/configuration changes in the launch result.

## 5. Change transfer and final handoff

- [x] 5.1 Implement complete selected-change copying to its owner's corresponding root, destination verification, and private atomic transfer receipts; verify current uncommitted files, metadata preservation, incomplete planning artifacts, conflicting inherited targets, missing schema/configuration, interrupted copies, and strict transfer-boundary containment.
- [x] 5.2 Register the output workset after worktree, store, pointer, and optional destination-change readiness; verify identical registration reuse, mismatch/race conflicts, preserved source on registration failure, and output membership containing only spawned roots.
- [x] 5.3 Implement default move cleanup after publication and the `--keep-source` alternative; verify source snapshot checks, new/modified source file preservation, partial deletion failures, destination preservation, unchanged Git indexes/no automatic commits, and distinct workspace-ready versus move-incomplete outcomes.
- [x] 5.4 Implement recovery from transfer receipts and observed state; verify repeated completed moves after destination edits, absent sources without evidence, interrupted cleanup, changed destinations before cleanup, and rejection of receipt paths or transfer modes inconsistent with the launch. Document manual recovery for preserved conflicts.

## 6. Product command surface

- [x] 6.1 Register `pspec workset add` and `pspec workset launch` with `--change`, `--store`, and `--keep-source`, human/JSON results, exit codes, store mappings, partial-error stages, and the OpenSpec opening command; verify dependent option validation, help without effects, operation outside a consumer, existing CLI-group regressions, and no editor spawn.
- [x] 6.2 Add user documentation for registration, indexed overrides, naming, all-store registration, pointer updates, default move/copy fallback, source-store disambiguation, cleanup/retry, and OpenSpec opening; verify documented commands against isolated workflows and explain remove/create append recovery.

## 7. End-to-end evidence

- [x] 7.1 Exercise the installed CLI with real Git repositories and an isolated OpenSpec registry: mixed target branches, remote bases, multiple stores, nested store roots, ambiguous changes, explicit source selection, move and keep-source, repeat after source removal, partial creation/registration/cleanup failures, and retries; record outputs and verify only the selected change is removed from source, original registrations remain intact, and the user's real worksets are untouched.
- [x] 7.2 Run the full `uv run pytest` suite after integration, validate this change with `openspec validate add-workset-launch --strict`, and review scenario coverage against the spec; verify later behavior revisions with focused tests and record their evidence.

## Verification evidence

- Full regression suite: `uv run pytest -q` — 358 passed, 1 skipped. Subsequent preflight aggregation and partial-result reporting refinements passed the focused checkout-view and transfer checks; store routing, schema failure, collision and CLI parsing checks also passed.
- Installed `pspec` tests used disposable real Git repositories and isolated `XDG_CONFIG_HOME` / `XDG_DATA_HOME` registries. Verified mixed branches, remote bases, nested stores, ambiguity selection, move/copy, completed retries, unchanged advisory checkouts and exclusion of unrelated temporal files.
- Failure injection covered worktree creation, store/output registration, copy interruption, source edits and partial cleanup. Receipt validation and destination edits preserved user work; tracked source removals did not change the Git index.
- `openspec validate add-workset-launch --strict` passed. Environment: OpenSpec 1.13.2, Git 2.55.0.windows.5, Windows, Python 3.12.
- User revision: task 2.3 now uses supported `workset remove --yes` followed by `workset create`, with original-definition restoration on failure. The former upstream append prerequisite has been removed. Verification covers order/tool preservation, retries, label conflicts, concurrent replacements, lost responses, failed removal and failed restoration, plus actual CLI append in an isolated registry.

- Append revision checks: 37 targeted tests passed (append recovery, launch planning, CLI parsing, and installed add); strict OpenSpec validation passed.

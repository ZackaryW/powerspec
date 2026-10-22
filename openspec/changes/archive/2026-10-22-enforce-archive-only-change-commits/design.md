# Design

## Context

See proposal.md for motivation. Existing incremental-checkpoints context encourages explicit staged slices but does not exclude planning. zmem-lifecycle shares one body between compile-time context and startup/compaction traits. The CLI uses thin Typer handlers. Git worktree helpers already wrap native Git, but intentionally discard GIT_INDEX_FILE and require HEAD for repository inspection, so they cannot inspect the exact index used by an unborn or alternate-index commit.

## Goals / Non-Goals

**Goals:** Establish a deterministic, read-only path preflight and deliver consistent commit governance through existing mechanisms. Preserve incremental verified code commits and local active artifacts.

**Non-Goals:** Automatic Git hook ownership/installation, interception of all git commits, remote enforcement, executing zmem inside Powerspec, proving archive or sync from filenames, rewriting existing history, or changing OpenSpec's upstream skill procedures.

## Decisions

### Read the index, not the staged diff or working tree

Use native Git plumbing with NUL-delimited stage records. All retained entries count, including unchanged tracked files and intent-to-add entries. Reject unmerged stages independently. Git expands sparse index directories for ordinary ls-files without --sparse. Do not write a tree object just to inspect it. Interpret path components lexically, with case-insensitive openspec/changes recognition and an exact archive child exception; support nested consumers across the repository. Reject boundary entries themselves, such as a symlink named openspec/changes or openspec/changes/archive.

### Portable helper and reuse assessment

Add `read_index(cwd: Path, *, timeout: float = 15) -> GitIndex` under src/powerspec/utils/git_index.py. GitIndex contains the absolute repository root and immutable entries of path, mode, object id and stage in native order. A release tool checking forbidden package files is another caller independent of OpenSpec. Errors use a dedicated ValueError subtype and preserve actionable native diagnostics.

Reuse subprocess.run with literal argument arrays, finite timeout, byte output and native Git rev-parse/ls-files. Preserve Git's environment, especially GIT_INDEX_FILE, so checks inside a commit hook or an alternate-index command observe the same selected index. Use --full-name with a top-anchored pathspec and -z for paths, retaining the invocation cwd for native relative Git environment semantics; disable optional index locking and fsmonitor during reads. Existing git_worktrees.git_bytes is unsuitable because it strips index selection; leave its mutation safety behavior unchanged. No new Git library is justified: Git already owns index formats, linked worktrees and sparse expansion. The only new mechanics are bounded execution and parsing its documented stage record format. Verify the helper with domain-neutral real Git fixtures before application integration.

### Application and CLI boundary

Application policy in powerspec/commit_check.py consumes entries and emits ok, repository, forbidden_paths, unmerged_paths and errors. Keep path rules out of the generic helper. A new check group registers commit with --json under both existing aliases. Exit 0 means the inspected index has no violations; exit 1 means violations or failed inspection, and invalid syntax remains Typer exit 2. Human errors go to stderr and JSON remains one object. No consumer/resource discovery, source acquisition, zmem execution or Git mutations occur.

### Governance and verification boundary

Update shared zmem-lifecycle prose to cover every commit and index preflight, retaining its existing runtime and failure behavior. Update incremental-checkpoints task/apply guidance and add archive guidance to sequence spec sync, archive, staging and validation. Publish through pspec sync rather than editing managed YAML by hand. Existing shared-body delivery tests plus semantic review cover prose; new real Git tests prove path decisions, exit codes and state preservation. They do not pretend text assertions establish agent adherence. Sync/archive success remains an agent workflow obligation; the checker is deliberately only a path preflight.

## Risks / Trade-offs

- An agent can omit the command or a user can commit directly: document explicit invocation and avoid claiming automatic interception.
- The index can change after a check: require checking immediately before committing and rerunning after staging changes; no transactional lock is promised.
- A folder named archive does not prove completed work: lifecycle guidance requires actual successful sync and archive independently.
- Ignored active files are not backed up by Git: preserve local content and explicitly explain the repository policy; do not delete planning or mark unfinished work complete.
- Git environment selects another index/repository: honor native selection and report the inspected root, matching Git's own commit context.

## Migration Plan

Add repository ignore rules for active change directories while permitting archive contents, including nested consumers. Explicitly remove the six already tracked migrate-zmem2-integration entries from this repository's index with local bytes preserved; this is a one-time scoped reconciliation, never automatic checker behavior. Stage those deletions with the first verified implementation slice so every new commit tree is clean. Keep both active changes on disk and leave main spec deltas uncommitted until their changes are actually synced and archived. Reverting the implementation is a normal reviewed commit; do not automatically restore active tracking or rewrite history.

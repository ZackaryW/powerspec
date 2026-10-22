# Tasks

## 1. Git index reader

- [x] 1.1 Implement the portable read-only Git index helper through TDD; verify domain-neutral real repositories cover unborn branches, whole-index nested invocation, alternate indexes, unusual names, linked worktrees, conflicts and state preservation.

## 2. Commit eligibility checkpoint

- [x] 2.1 Implement path eligibility and both CLI aliases through TDD; verify real Git outcomes for staged and previously tracked active files, archives, forced ignored additions, nested consumers, intent-to-add, failures and preserved state; document the command and its evidence limits.
- [x] 2.2 Reconcile this repository's tracked active artifacts and ignore rules while preserving every local file; verify archive paths remain addable, no active entries remain in the proposed index, and the verified implementation checkpoint follows zmem without committing active artifacts.

## 3. Governance checkpoint

- [x] 3.1 Update shared standing, task/apply and archive guidance for every-commit zmem use, incremental code checkpoints, index preflight and sync-before-archive artifact commits; verify semantic consistency and existing context/startup/compaction delivery tests, publish with pspec sync and verify repeat publication is unchanged.
- [x] 3.2 Run affected integration and CLI checks, validate this OpenSpec change, and inspect the final index and committed trees; record actual behavioral evidence and limits before the zmem-authored governance checkpoint.

## Workflow follow-up

- Completed 2026-10-22: synchronized all six requirements into the new commit-governance main spec, validated it strictly, and archived this change before staging its artifacts. All 17 main specs passed normal validation; pre-existing long-requirement warnings remain in other capabilities. Post-archive temporal cleanup reported unchanged because no matching values existed.
- The separate migrate-zmem2-integration change remains available locally for its own sync/archive; removing its tracked entries does not imply archival completion.

## Verification evidence

- Git index helper: observed missing-behavior failures before implementation; 7 focused tests passed after implementation. Fixed alternate-index and Windows filename fixture assumptions separately from production behavior.
- Commit CLI: observed failures through both installed console aliases before command registration. Real Git fixtures cover existing tracked artifacts, forced additions, intent-to-add, nested consumers, case/path boundaries, unusual names, linked worktrees, alternate indexes, sparse indexes, conflicts and unchanged state. A disposable explicit pre-commit hook rejected a Git commit and preserved HEAD.
- Repository ignore rule: observed active files incorrectly entering `git add .`, then verified both root and nested active planning stay local and archives remain addable. The six previously tracked migration files were hash-verified unchanged after index-only removal.
- `uv run pytest tests/test_git_index.py tests/test_commit_check.py tests/test_cli.py -q --tb=short`: 62 passed.
- `uv run pytest tests/test_resources.py tests/test_sync.py tests/test_hooks.py tests/test_hook_input.py tests/test_guidance_bodies.py tests/test_guidance_doctor.py tests/test_catalog.py tests/test_doctor.py -q --tb=short`: 129 passed, 4 skipped. These affected suites were selected instead of rerunning the unrelated full suite.
- `pspec sync` updated owned configuration; the second invocation reported unchanged. Live Codex startup and compaction resolution produced the updated shared policy. Existing delivery tests and semantic review support publication/delivery, not agent adherence.
- `openspec validate enforce-archive-only-change-commits --strict` passed. Implementation checkpoint 85ad09c passed zmem message validation and post-commit inspection; its tree contains no active change entries.
- Governance checkpoint 0213a61 also passed zmem validation and post-commit inspection, including its durable decision. Its committed tree contains no active change entries.
- The checker is explicit and read-only. No Git hook was installed outside disposable test repositories. It cannot prove actual sync/archive completion or zmem use, and cannot prevent direct commits that omit it or index changes after inspection.

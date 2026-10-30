# Tasks

## 1. One-project dispatch

- [x] 1.1 Rewrite the multi-project tests in `tests/test_hook_antigravity.py` through the CLI entrypoint: two consumers without a default list both paths and the command with neither guidance body; paths resolving to one consumer (two paths in one repository, one consumer beside a plain folder) deliver its guidance unlabeled; one malformed of three consumers is named on stderr and left out of the list; all failing exit 1; a seven-consumer workset of 6,000-character bodies delivers none of them. Verify the new assertions fail
- [x] 1.2 Rewrite `tests/test_hook_workset_default.py`: a matching default delivers only its guidance and is marked in the list; a default without guidance is named with no section; a default whose guidance fails is named on stderr and the list still delivered; subset, absent, ambiguous, and malformed defaults deliver no guidance body; OpenSpec is never invoked. Verify they fail
- [x] 1.3 Implement D1-D4 in `src/powerspec/cli/hook.py` and verify 1.1, 1.2, and the remaining hook suites pass

## 2. Documentation

- [x] 2.1 Update the Antigravity multi-project text in `docs/hook-delivery.md` and the default member paragraph in `docs/worksets.md`; run the documented per-project command from a temporary consumer and confirm it prints only that project's guidance

## 3. Verification

- [x] 3.1 Run the full `uv run pytest` suite (known Codex CLI failures excepted) and `openspec validate single-project-hook-guidance --strict`
- [x] 3.2 Real session: open a real `agy -p --add-dir` session over two consumers with and without a default and record which guidance reached the agent

## Workflow follow-up

- Commit 1.x and 2.x as code and docs checkpoints with `pspec check commit` and zmem validation, excluding this change's artifacts; archive, validate main specs strictly, then make the artifact commit and run `pspec state clear --change single-project-hook-guidance`.

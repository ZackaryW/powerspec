# Tasks

## 1. Defaults file and matching

- [x] 1.1 Write failing tests in `tests/test_workset_defaults.py` for the file model: read missing file as empty, round-trip set/clear preserving other worksets, atomic replacement keeps the old content on failure, malformed TOML raises a typed error; verify they fail for the missing module
- [x] 1.2 Write failing tests for path normalization and matching: forward versus back slashes, drive-letter case, spaces and parentheses, exact set match, subset and superset rejected, two matching entries reported ambiguous; verify they fail
- [x] 1.3 Implement `src/powerspec/workset_defaults.py` per `design.md` D1-D2 using `utils/atomic.replace_bytes`, and verify 1.1 and 1.2 pass

## 2. `pspec workset default` command

- [x] 2.1 Write failing CLI tests with a fake OpenSpec adapter: set, repeat-set unchanged without rewrite, show current, clear, clear absent, unknown workset, non-member label listing members, OpenSpec failure, and `--json` single-object output; assert the adapter received no create/remove calls
- [x] 2.2 Write failing tests for show staleness reasons (workset removed, label removed, members changed) with their fix-it hints
- [x] 2.3 Implement the command in `src/powerspec/cli/workset.py` and verify 2.1 and 2.2 pass

## 3. Launch and append carry-over

- [x] 3.1 Write failing tests in the workset launch suite: a current source default is recorded for the published output with the new worktree path; an identical output entry is reused; a different existing output default is kept and reported; an unpublished launch records nothing; a stale source default records nothing
- [x] 3.2 Write failing tests for `add`: a successful append refreshes the snapshot of a current default; a failed append and a stale default leave the entry unchanged
- [x] 3.3 Implement the launch and append hooks per `design.md` D4 and verify 3.1, 3.2, and the existing workset suites pass

## 4. Hook integration (gated on `support-antigravity-hooks`)

- [x] 4.1 After `support-antigravity-hooks` is implemented, write failing tests for multi-project dispatch: exact match names the default and marks its section; a default without guidance is named without an empty section; subset payload and no file give no default; malformed file reports on stderr, still delivers sections, exits zero; and a fake that fails if OpenSpec is invoked during default lookup
- [x] 4.2 Mark the default section through its caller-supplied label (no `compose_sections` change needed), implement the default-aware instruction in the hook, and verify 4.1 passes

## 5. Documentation and integration

- [x] 5.1 Document the command, the file, staleness, and the launch and append behavior in `docs/worksets.md`, and the fallback instruction in `docs/hook-delivery.md`; verify each documented command runs against a temporary home
- [x] 5.2 Run `uv run pytest` and `openspec validate add-workset-default-project --strict`; verify both are green
- [x] 5.3 End to end: set a default on a temporary two-repository workset, launch it, open the output in an Antigravity session (`agy --add-dir` if `openspec workset open` has no Antigravity tool id), and verify the delivered message names the default; record the observation, noting that delivery is not adherence

## Workflow follow-up

- Every authorized commit follows the zmem commit-authoring skill and requires a passing `pspec check commit` immediately beforehand; active change artifacts stay out of code checkpoints.
- Archive after `support-antigravity-hooks` is archived, then run `pspec state clear --change add-workset-default-project`.

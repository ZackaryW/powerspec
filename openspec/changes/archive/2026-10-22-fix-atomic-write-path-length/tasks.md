# Tasks

## 1. Correct and verify the shared atomic writer

- [x] 1.1 Change `replace_bytes` to use a short destination-independent staging prefix while retaining exclusive same-directory creation, flush/fsync, replacement, no-op behavior, and cleanup. Add a domain-neutral real-filesystem regression with an independently verified valid long destination and short-sibling support; demonstrate that it catches the original naming failure and passes with the correction using `uv run pytest tests/test_atomic.py`.
- [x] 1.2 Strengthen cleanup assertions to inspect directory contents independently of temporary naming; verify successful publication, unchanged-content metadata, preservation of existing bytes on publication failure, no staging residue, and missing-parent handling. Document the bounded staging rationale in the helper and pass all atomic-writer tests before application acceptance checks.

## 2. Verify workset transfer and retry compatibility

- [x] 2.1 Reuse or extend isolated workset transfer tests to exercise initial receipt publication failure through the shared writer, followed by a successful retry. Verify source/worktree preservation, no incomplete output workset, reuse of prepared worktrees, and completion receipts recognizing retries without overwriting later destination edits; keep receipt identities, locations, and schema unchanged.
- [x] 2.2 Run `uv run pytest tests/test_workset_installed.py::test_installed_multirepo_move_copy_and_retry` on the affected Windows host under its ordinary pytest root, with no diagnostic prefix shim or shortened `--basetemp`. Verify move, copy, and repeat launch success, and record the result and host path-policy context in this change's verification notes.

## 3. Complete integration validation

- [x] 3.1 Run affected workset and shared-writer caller checks, then `uv run pytest` once for cross-cutting integration. Record outcomes and any independently demonstrated unrelated failures in the change's verification notes; preserve test registry/environment isolation and do not change host path policy to obtain a pass.
- [x] 3.2 Review the implementation against the spec delta and portable helper contract, verify no receipt migration or caller-specific workaround was introduced, and run `openspec validate fix-atomic-write-path-length --strict --no-interactive`. Record final verification and keep task completion aligned with observed evidence.

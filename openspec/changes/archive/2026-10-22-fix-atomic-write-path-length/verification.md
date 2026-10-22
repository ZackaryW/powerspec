# Verification

## Implemented behavior

`replace_bytes` now uses a short `.pspec-` staging prefix independent of the target basename. Exclusive creation, sibling placement, flushing/fsync, atomic replacement, unchanged-content no-ops, and existing error/cleanup handling remain intact. Receipt hashing, locations, JSON schema, and application callers are unchanged. The implementation checkpoint is commit `4983f58`.

## Observed regression and acceptance evidence

- On 2026-10-21, `uv run pytest tests/test_atomic.py -q` before the production fix produced **1 failed, 3 passed**. The new boundary test independently created a valid 256-character destination and a short sibling, then failed in the original staging-name creation with `FileNotFoundError`. After the fix the same command produced **4 passed**. Cleanup assertions inspect actual directory entries instead of matching the old prefix.
- The new receipt-publication failure/retry test and `tests/test_workset_installed.py::test_installed_multirepo_move_copy_and_retry` together produced **2 passed in 30.39s**. The installed executable was exercised under the ordinary pytest temporary root, without a shortened `--basetemp` or diagnostic prefix shim. The selected Python environment imports the changed helper from this checkout.
- The receipt failure test reaches the real shared writer and injects failure only at receipt replacement. It observes unchanged source contents, preserved worktree, no output workset, and no staging residue. Removing the fault permits reuse and a completed receipt at the originally attempted path; another retry preserves later destination edits.
- Windows `LongPathsEnabled` was **0**, also confirmed on 2026-10-22. No operating-system policy or persistent environment changes were made. Host limits still apply to the actual destination and short sibling paths.

## Broader checks

On 2026-10-22, the affected atomic, workset, configuration, temporary-state, sync, and sources test files produced **119 passed, 2 skipped in 120.71s**. The earlier broader-check tool session ended without a returned result, so it is not counted as evidence; this completed rerun is recorded in the ignored local log `build/atomic-focused-tests.log`.

`openspec validate fix-atomic-write-path-length --strict --no-interactive` passed. Diff review confirms the only production change is the staging prefix and its explanatory comment; no receipt migration or caller-specific workaround was introduced.

The full suite, `uv run pytest -q`, completed on 2026-10-22 with **551 passed, 18 skipped in 194.50s**, with no failures. Output is retained locally in `build/atomic-full-tests.log`. These are default-suite results; skipped optional/platform checks are not claimed as executed.

The `workset-launch` delta was synced into the main specification. Comparison confirmed the complete modified requirement and all five scenarios match, retaining the three existing scenarios. `openspec validate --specs --strict --no-interactive` passed for **all 15 main specifications**. All six implementation tasks are complete.

Archived on 2026-10-22 after sync verification. `uv run pspec state clear --change fix-atomic-write-path-length` succeeded and reported unchanged; there was no matching temporal state to clear.

## Commit-memory limitation

The selected `zmem` executable is the legacy Python runtime, which does not provide the Node engine's `check --file` interface. Commit messages were reviewed against the diff and test evidence; computed-memory validation and Node-runtime post-commit inspection are unavailable. No runtime or memory-data migration was attempted.

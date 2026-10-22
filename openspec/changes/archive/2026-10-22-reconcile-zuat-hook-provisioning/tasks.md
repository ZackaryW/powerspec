# Tasks

## 1. ZuAT dependency

- [x] 1.1 Pin published ZuAT 0.1.2 commit and refresh uv.lock; verify locked installation metadata and existing hook/provisioning tests.

## 2. Hook reconciliation

- [x] 2.1 Implement complete-inspection decision table and explicit receipt repair; verify real Codex and Claude adoption, stale-receipt repair, byte/mtime preservation, repeat reuse, legacy ambiguity and duplicate rejection, plus provider failure/operation ID propagation.
- [x] 2.2 Document normal reconciliation, explicit repair limits, and unresolved-conflict handling in hook-delivery.md; verify examples agree with public API behavior.

## 3. Upgrade integration

- [x] 3.1 Thread separate --repair-hooks authorization and display hook operation IDs; verify actual CLI parsing/output/exit behavior and upgrade preservation of obsolete skills when hook repair is unauthorized or ambiguous.
- [x] 3.2 Document upgrade repair invocation and skill-only --force boundary; verify CLI help matches documentation.

## 4. Integration verification

- [x] 4.0 Reconcile the immutable ZuAT pin and lockfile to the published correction from restore-missing-owned-hooks; verify installation from that revision without a local override.
- [x] 4.1 Run full pytest suite, locked dependency check, strict OpenSpec validation, and diff review; record results and any material limitations.

## Evidence

- Final full integration run: `uv run --with ./build/zuat-guard-1022/zuat-0.1.2-py3-none-any.whl pytest -q --tb=short` passed 589 tests, with 18 skipped. Strict OpenSpec validation, `uv lock --check`, and diff review passed. This verifies the corrected local wheel; this preceded publication and final Git dependency verification. No local override was added to pyproject.toml or uv.lock.

- ZuAT 0.1.2 pin/lock install succeeded; 43 existing hook/provisioning tests passed after creating native configuration directories in isolated fixtures.
- Exact-unowned adoption failed for both Codex and Claude before implementation and passed afterward.
- CLI repair-option tests failed before wiring and passed afterward.
- 82 focused hook/CLI/upgrade tests passed against a built local ZuAT package containing restore-missing-owned-hooks.
- Installed CLI help, lock consistency, and strict OpenSpec validation passed.
- The user approved a provider-side receipt-only guard. Both Codex and Claude race tests reproduced native replacement before wiring; both now preserve concurrent baseline restorations through `update_asset(force=True, receipt_only=True)`. Hook/CLI checks: 35 passed using the freshly built wheel at `build/zuat-guard-1022/zuat-0.1.2-py3-none-any.whl`; all 75 packaged Python files match the current ZuAT source. Earlier source-directory overrides reused a cached build and are superseded by the explicit-wheel checks.

- Published dependency verification: ZuAT commit b2cb2dc72d31a0aed5b55d5597fc2f56e3017941 was pushed to origin/main. Updated pyproject.toml and uv.lock; uv sync --locked rebuilt from Git successfully. Installed direct_url.json identifies that exact revision and the public update_asset signature includes receipt_only=False, without a local override.

- Final published-revision suite: uv run --locked pytest -q --tb=short passed 589 tests with 18 skipped in 229.40 seconds against Git revision b2cb2dc72d31a0aed5b55d5597fc2f56e3017941, without a local package override. Strict OpenSpec validation, locked dependency check, and diff whitespace checks passed.

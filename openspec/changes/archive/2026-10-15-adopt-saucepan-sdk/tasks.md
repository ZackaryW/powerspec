# Tasks

Checkpoint only coherent, verified slices. If replacing the SDK dependency breaks still-unconverted imports, complete the dependent adapter conversion before committing that slice; do not add legacy compatibility shims to manufacture an intermediate checkpoint. Keep active OpenSpec change files outside implementation commits and do not push without explicit authorization.

## 1. SDK and binary contract checkpoint

- [x] 1.1 Update the immutable SDK dependency to commit 041e4f90634e6007b58054a59604396f8fbebd21 and uv.lock; verify current Client import/construction and injected client isolation in a disposable environment.
- [x] 1.2 Replace removed shared_executable_path imports in saucepan_tool.py/doctoring.py with app-owned resolution and test 0.9 version/command checks, build suffixes, rejected legacy binaries and manager/shim asset selection.
- [x] 1.3 Update the Zuu compatibility policy identity while preserving 24-hour checks and compatible fallback; use focused test_saucepan_tool.py/test_doctor.py cases to verify cache invalidation and no provisioning under lookup deadlines.
- [x] 1.4 Update executable/dependency setup guidance and validate the documented explicit-binary path; retain existing installed pspec and live user stores throughout testing.

## 2. Scoped source adapter checkpoint

- [x] 2.1 Replace legacy view/history/token payloads in sources.py with current SDK models, stable app registration and explicit consumer scopes; verify same-recipe deduplication, two-consumer isolation and denied scope behavior in test_sources.py.
- [x] 2.2 Thread owning-consumer scope through workspace/status/hook/upgrade callers and persist canonical scope identity; test nested cwd stability, separate consumers, explicit moved-project rebind and aliases never becoming apps.
- [x] 2.3 Translate profile recipes to registered Source and Selector and preserve SourceBinding provenance/contained views; test exact reference/commit, ambiguous/mismatched source results and no reconstructed store paths.
- [x] 2.4 Replace diagnostic substring decisions with domain codes and TransportError uncertainty mapping; test missing metadata, corrupt records, access denial, revision conflict and no unbound retry.
- [x] 2.5 Document scope and optional credentials/integrity choices alongside the existing source syntax; run targeted source/consumer tests and verify no authored profile migration is required.

## 3. Pinned lifecycle checkpoint

- [x] 3.1 Register immutable flat policies and prepare scoped groups with generation pin receipts on authorized ensure paths; test fresh init, missing-only acquisition, repeated-init no refresh and real-manager keyring-free operation.
- [x] 3.2 Add consumer-owned binding/receipt publication and reconcile uncertain mutations by original key/revision; test lost responses and failure before local publication preserving prior selected bindings.
- [x] 3.3 Implement read-only lookup of selected retained outputs under the existing inspection deadline; test that sync/status/hooks invoke no mutating SDK operations even for missing or corrupt resources and concurrent reclaim.
- [x] 3.4 Wire explicit upgrade candidates through catalog/selector validation and existing ZuAT provisioning/removal boundaries; test failed refresh/provisioning preserving old selected outputs and obsolete installed copies.
- [x] 3.5 Retain prior generations conservatively until explicit reader-safe cleanup and document pin ownership/recovery; test that one consumer cannot release another's pins and no automatic pruning races lookup.

## 4. CLI and distribution integration checkpoint

- [x] 4.1 Extend real-binary test_sources_integration.py with init -> changed local origin -> read-only lookup unchanged -> upgrade -> new selection across two isolated consumers; verify complete source provenance and no network dependency.
- [x] 4.2 Exercise actual Typer entrypoints for init/sync/status/upgrade/hook error paths, stdout/stderr and exit codes using the repository's pspec-tdd process for behavioral segments; run affected sources/sync/hooks/doctor tests before broader pytest checks.
- [x] 4.3 Build/install the distribution outside the checkout with its pinned SDK and an explicit compatible executable; verify no old Saucepan/shared_executable_path imports or protocol fallback remains and document any release availability limit.
- [x] 4.4 Validate the change strictly and reconcile remote-sources/managed-binary documentation with demonstrated lifecycle behavior without altering packaged builtin source policy.

## 5. Saucepan 0.10 profile adoption checkpoint

- [x] 5.1 Pin SDK 0.2.0 to release commit 8a2d04e7d2e393c035715520254bdd5955651873, require the 0.10 manager profile command surface, and update binary check identity/documentation.
- [x] 5.2 Expand the Rust explicit-update profile on authorized preparation only, register its flat catalog, and add only explicit upgrade and retention policies. Preserve read-only lookup, consumer scope, optional protection, and pinned selections.
- [x] 5.3 Save expanded policy records and UUID refs with pending intent; verify lost-response retries reuse that snapshot rather than re-expanding a recipe.
- [x] 5.4 Verify focused and real-manager lifecycle tests plus an installed distribution against the published 0.10.0 manager and SDK assets, recording provenance and any release availability limitation.

## Saucepan 0.10 verification evidence

- Full source suite: `uv run --frozen pytest -q` — 472 passed, 3 opt-in real-manager tests skipped, in 326.22 seconds. The skipped cases were separately exercised against the published manager as recorded below.
- Source checks: 46 focused source/binary/doctor/migration tests passed. Observed red for missing manager expansion and the old 0.9 gate before production changes. Three provisional lifecycle tests also passed against a local development manager before release availability.
- Published release: `v0.10.0`, manifest commit `8a2d04e7d2e393c035715520254bdd5955651873`; Python SDK 0.2.0. The Windows x64 release executable reports `saucepan 0.10.0+v0.10.0`.
- Verified release manager ZIP SHA256 `864c04e0f7990f61c90521db440dfbaa8a30e2e05a9cada25816a837d0d5ba7a`; published wheel SHA256 `0d2ec50225674a07f168d88c7ea8a5692726eb3c652314222e0f18cb8ae0325e`. The wheel matches sdk-manifest.json and the ZIP matches SHA256SUMS.
- Published-manager integration: `SAUCEPAN_TEST_BINARY=<published-v0.10.0>/windows-x64/saucepan.exe uv run --frozen pytest tests/test_sources_integration.py -q` — 3 passed. Covers flat policy registry lookup, adopted claim explanation, manual initialization versus explicit upgrade override, real Typer init/sync/upgrade, isolated consumers, rejected candidates, lost responses, concurrent reclaim and retained paths.
- Built PowerSpec wheel, installed it with the declared immutable Git SDK dependency in a disposable directory, then replaced the SDK with the checksum-verified published wheel. Ran copied tests through isolated Python with imports verified from site-packages: `python -I -m pytest tests/test_sources_integration.py tests/test_sources.py tests/test_saucepan_tool.py tests/test_sdk_migration.py -q` — 46 passed. The actual published manager passed Powerspec's executable version and command probes.
- Host verification: Windows x64, Python 3.12.13. Linux/macOS, other Windows architectures and opt-in native keyring verification were not exercised. No live consumer stores, installed user commands, remote repositories, tags or hosted workflows were changed.
- Local checkpoints: `755b225` (profile adoption) and `8de8b00` (published contract regression coverage). Zmem message checks passed; active OpenSpec files remain outside implementation commits.

## Earlier verification evidence

- Final full suite: `uv run --frozen pytest -q` — 468 passed, 3 skipped (the opt-in real-manager integration cases).
- Explicit current-manager run: `SAUCEPAN_TEST_BINARY=<saucepan-2>/target/debug/saucepan.exe uv run --frozen pytest tests/test_sources.py tests/test_sources_integration.py -q` — 25 passed. Covers real Typer init/sync/upgrade, isolated consumer receipts, lost-response reconciliation, rejected candidate recovery, and concurrent reclaim with retained reads.
- Built the wheel, installed it with the immutable Git SDK dependency into a disposable environment, and acquired/committed/looked up a local Git resource from outside the checkout using an explicit manager path.
- `openspec validate adopt-saucepan-sdk --strict` and `git diff --check` passed. No legacy Saucepan SDK imports, protocol fallback, or unbound lookup retry remains.
- Behavioral work used the installed pspec-tdd procedure directly with the user's explicit exception for the resolver's manifest mismatch. Initial version-contract and consumer-scope failures were observed before implementation; subsequent regression coverage was extended during integration.
- Execution was on Windows. Release asset selection covers the supported Windows, Linux, and macOS names; Zuu's executable-mode handling was inspected, but native Unix runtime verification was not performed here. Tests used the current local 0.9 manager and do not assert remote release availability.
- Local checkpoints: 612c885, 5592a7f, 9159a2a, 6ce8ea4. Active OpenSpec artifacts remain excluded; no push or archive was performed.

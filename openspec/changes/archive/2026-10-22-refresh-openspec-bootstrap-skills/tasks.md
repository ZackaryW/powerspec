# Tasks

## 1. Bundled workflow compatibility

- [x] 1.1 Pin the twelve bundled skill roots to OpenSpec v1.14.3 and align bootstrap/doctor compatibility and documentation; observe red/green version-boundary tests and pass focused initialization, doctor, and build-source checks.

## 2. Generated skills

- [x] 2.1 Refresh repo-local skills through openspec update; inspect generated target/version changes and verify repeat update is unchanged while preserving unrelated authored files.

## 3. Distribution verification

- [x] 3.1 Build a direct wheel and sdist, rebuild offline, compare full packaged catalog bytes/provenance, and verify installed-wheel bootstrap and skill availability in an isolated consumer without a source override.
- [x] 3.2 Run the full test suite, lock consistency, strict change validation, and diff checks; record results and create the final local checkpoint without pushing.

## Evidence

- Compatibility red/green: 5 targeted cases failed before the version-floor change. Initialization, doctor (including CLI JSON), guidance doctor, and build-source tests then passed: 57 passed, 1 skipped. No portable helper was added; existing version parsing and snapshot acquisition remain in use.

- Generated skills: official openspec update refreshed the existing 11 Codex workflows from 1.12.0 to 1.14.3. A second update reported up to date and preserved every generated file byte. The optional local onboard workflow was not newly enabled; all 12 declared workflows remain bundled.

- Distribution: direct wheel and sdist built from the pinned public source without POWERSPEC_OPENSPEC_SOURCE. An explicit offline build from the sdist succeeded. All 48 catalog files matched byte-for-byte between wheels; all 12 OpenSpec skill roots and upstream revision provenance were verified, and sdist manifest hashes matched the wheel.

- Installed-wheel check: installed the direct wheel and lockfile-exported dependencies into build/openspec-1143/venv. Imported Powerspec from that venv, compared installed catalog bytes, bootstrapped a fresh isolated Git consumer using OpenSpec 1.14.3 with tools disabled, and verified repeat initialization preserved every consumer file. The installed pspec resolve skill entrypoint returned null for the ordinary packaged OpenSpec skill as expected.

- Final integration: uv run --locked pytest -q --tb=short passed 594 tests with 18 skipped in 211.46 seconds. Lock consistency, strict OpenSpec change validation, and diff whitespace checks passed. Commits are local only. Computed zmem validation was unavailable because the selected executable is the incompatible older runtime.

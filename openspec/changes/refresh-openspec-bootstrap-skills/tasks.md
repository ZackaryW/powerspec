# Tasks

## 1. Bundled workflow compatibility

- [x] 1.1 Pin the twelve bundled skill roots to OpenSpec v1.14.3 and align bootstrap/doctor compatibility and documentation; observe red/green version-boundary tests and pass focused initialization, doctor, and build-source checks.

## 2. Generated skills

- [ ] 2.1 Refresh repo-local skills through openspec update; inspect generated target/version changes and verify repeat update is unchanged while preserving unrelated authored files.

## 3. Distribution verification

- [ ] 3.1 Build a direct wheel and sdist, rebuild offline, compare full packaged catalog bytes/provenance, and verify installed-wheel bootstrap and skill availability in an isolated consumer without a source override.
- [ ] 3.2 Run the full test suite, lock consistency, strict change validation, and diff checks; record results and create the final local checkpoint without pushing.

## Evidence

- Compatibility red/green: 5 targeted cases failed before the version-floor change. Initialization, doctor (including CLI JSON), guidance doctor, and build-source tests then passed: 57 passed, 1 skipped. No portable helper was added; existing version parsing and snapshot acquisition remain in use.

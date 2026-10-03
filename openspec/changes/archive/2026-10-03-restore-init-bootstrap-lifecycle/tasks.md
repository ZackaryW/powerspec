## 1. Restore initialization bootstrap

- [x] 1.1 Add optional agent provisioning to init, remove the install command, and preserve partial setup for retry; verify public CLI tests for empty profiles, scopes, repeated initialization, invalid agents, and failures. Update setup, hook, and skill docs and bundled bootstrap guidance.

## 2. Prepare missing sources during sync

- [x] 2.1 Handle native missing secrets through Saucepan's guarded initialization and switch sync to ensure without refresh; verify missing/existing source, failure-preserves-YAML, and credential-guard tests. Update source and sync documentation.

## 3. Verify the complete lifecycle

- [x] 3.1 Exercise fresh init, repeat setup, sync revision reuse, and explicit upgrade with isolated agent homes, registries, and a real Saucepan test store; verify focused regression suites and built-wheel entrypoints, then validate the change strictly.

## Verification evidence

- Focused CLI, initialization, provisioning, sync, source, workspace, upgrade, packaged-resource, and managed-binary tests: 114 passed with the real Saucepan integration tests enabled.
- Regression cycles observed failing before implementation for init provisioning, removal of install, sync source policy, and native missing-secret handling.
- Real Saucepan test-store lifecycle: first sync acquisition, init provisioning/reuse, unchanged source revision on repeated sync, and new source content after explicit upgrade.
- Built wheel installed outside the checkout with dependencies reused from the development environment; both console aliases, real OpenSpec bootstrap, user-scoped agent installation, repeated init, and sync passed in a disposable repository/home/ZuAT registry. This is not a clean dependency-resolution test or verification of another machine's native credential service.
- Strict OpenSpec validation passed. Existing store rejection is covered without replacing secrets or deleting data.
- The full project suite exercised 378 tests: 375 passed, two were skipped, and one stale help-contract assertion still named the removed install command. After correcting that assertion, the affected CLI suites passed 52/52.

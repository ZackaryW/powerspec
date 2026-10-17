# Tasks

## 1. Default store bootstrap and recovery checkpoint

- [x] 1.1 Observe failing bootstrap regressions, implement feature-owned orchestration and default-path wiring, and pass focused tests for ordering, preservation, unknown/linked paths, initialization/publication failures, retry, concurrency, cache reuse, explicit overrides and read-only behavior.
- [x] 1.2 Document first-run ordering, backup preservation and stale-lock recovery in remote-source instructions; review the implementation diff and create a focused zmem checkpoint excluding active OpenSpec artifacts.

## 2. Diagnostics and real-manager integration checkpoint

- [x] 2.1 Observe a failing doctor regression, clarify human/JSON executable-only results without changing check names or mutation behavior, update README troubleshooting, and pass doctor/CLI tests.
- [x] 2.2 Add and run isolated actual-manager acceptance tests through default provisioning for fresh and binary-only roots, source acquisition, repeated init and upgrade; run a live official-release bootstrap and record its evidence.
- [x] 2.3 Run the affected source/initialization/inspection suites and strict OpenSpec validation, inspect the complete diff, and checkpoint verified integration/docs with zmem while excluding active change artifacts.

## 3. Installed consumer verification

- [x] 3.1 Reinstall the verified local PowerSpec package, verify its installed dependency/binary boundary, and retry the interrupted user init command; report source/bootstrap results and any separate agent-installation failures accurately without pushing or archiving.



## Verification evidence

- Observed eight failing default-bootstrap regressions before implementation; bootstrap and managed-tool checks then passed (34 tests).
- Observed failing human/JSON doctor diagnostic regressions before clarifying executable-only readiness.
- Affected bootstrap, actual-manager, source, initialization, inspection and doctor suites: 109 passed. Canonical GitHub identity follow-up: 28 source tests passed after an observed casing regression.
- Actual Saucepan 0.10.0 CLI and SDK passed default-path fresh and binary-only recovery, source acquisition, repeated init and upgrade tests in isolated homes. No SDK client was injected into those default-path tests.
- An isolated live official-release download initialized its store and reused the manager successfully. Built and installed the local PowerSpec wheel, verified installed PowerSpec 0.1.4, SDK 0.2.0, Zuu 202609.29.0 and ZuAT 0.1.1.
- Retried the user's Saucepan consumer with installed `pspec init --agent codex`: shared-store bootstrap and both remote source acquisitions succeeded. Existing unowned native skills and a hook ownership conflict prevented agent provisioning. Those assets were not overwritten; this is separate from the bootstrap fix and is not claimed as setup success.
- The original binary-only bin directory remains in the user's `.powerspec-saucepan-backup-9616098095da484698560afc347bd46f` backup. No push performed.
- Local verified checkpoints: ac693a8 (bootstrap), b72de10 (diagnostics/integration), 8567061 (GitHub canonical identity).
- Follow-up installed `pspec init` (source-only) completed successfully in the Saucepan consumer and retained source selections; existing conflicting agent assets remain untouched.

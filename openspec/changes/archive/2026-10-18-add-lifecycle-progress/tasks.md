# Tasks

## 1. Reusable heartbeat checkpoint

- [x] 1.1 Observe failing tests for portable progress events, waiting, nesting, failure/interruption and observer/thread cleanup; implement and verify utils/progress.py before application wiring.
- [x] 1.2 Review and zmem-checkpoint the verified utility, excluding active change artifacts.

## 2. Lifecycle integration checkpoint

- [x] 2.1 Observe failing application/CLI tests, add feature-owned stderr reporting and instrument init/upgrade, source-only init, manager/source stages, individual skills, hooks and publication/removal/recovery while preserving operation contracts.
- [x] 2.2 Verify live-before-completion output and failure/timeout context through actual CLI subprocesses, confirm protocol/stdout isolation and unchanged ownership/recovery semantics, and document progress and evidence limits.
- [x] 2.3 Run affected lifecycle/source/provisioning/upgrade/protocol suites and strict OpenSpec validation; inspect the diff and create a zmem integration checkpoint excluding active artifacts and the unrelated .gitignore edit.

## 3. Installed command evidence

- [x] 3.1 Build and install the local wheel, demonstrate progress before an isolated blocked operation completes using the installed command, and record results without forced live adoption, archive, tags or pushes.



## Verification evidence

- Utility RED: eight focused behavior tests failed before implementation; all ten utility tests passed after implementation, including nested waiting and interruption cleanup. Utility checkpoint: e046202.
- Application RED: three CLI progress assertions failed before wiring. Init, bootstrap and native provisioning checks then passed (21 tests); upgrade regressions passed (13 tests).
- Live-output acceptance: eight CLI/application tests passed, including actual subprocesses held open until a waiting line was observed. Both success and timeout paths preserved stdout/results and original failure context. A returned skill conflict was observed before the next skill inspection.
- Built the wheel and installed it in an isolated environment. Both installed init/upgrade entrypoints emitted a real five-second waiting event before controlled work completed. The installed pspec.exe performed source-only init in a disposable Git consumer with progress on stderr. Installed doctor JSON remained parseable without lifecycle progress.

- Full regression run with the real-manager acceptance tests enabled: 544 passed, 1 skipped in 382.95 seconds. Strict change validation passed. Installed the verified local wheel into the user PowerSpec tool environment for subsequent commands.

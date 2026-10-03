# Tasks

## 1. Establish managed-tool behavior

- [x] 1.1 Add focused failing tests for manager policy, default-client provisioning, failure translation, and explicit-client bypass. Observed collection fail because `powerspec.saucepan_tool` did not exist.
- [x] 1.2 Implement the SDK-compatible Zuu managed-release configuration and connect it lazily to default Saucepan source clients.
- [x] 1.3 Run focused lifecycle and source tests, then record the verified checkpoint. `uv run pytest tests/test_saucepan_tool.py tests/test_sources.py tests/test_sync.py tests/test_initialization.py -q` passed 37 tests; strict change validation passed.

## 2. Document and verify integration

- [x] 2.1 Document automatic Saucepan installation, cached compatible upgrades, first-use failure behavior, and lazy activation in the remote-source guide.
- [x] 2.2 Exercise a real managed installation at the SDK shared path and confirm the resulting executable works through the SDK boundary. Zuu installed Saucepan 0.5.0 at `~/.saucepan/bin/saucepan.exe`, validated its version/help surface, wrote matching check state, and reused it on the second ensure.
- [x] 2.3 Run the full test suite and strict OpenSpec validation. `uv run pytest -q` passed 257 tests with one opt-in acceptance skipped; `openspec validate manage-saucepan-binary --strict` passed.


## 3. Correct compatibility policy

- [x] 3.1 Replace SDK-major/minor equality with the verified Saucepan CLI 0.5 and 0.6 compatibility range.
- [x] 3.2 Re-run focused lifecycle tests, the full suite, builds, and strict OpenSpec validation. Final suite: 265 passed and one opt-in test skipped; 34 focused source/sync/upgrade tests passed; wheel and sdist builds succeeded; strict validation passed; real Saucepan 0.5 clean-store and current-user-store flows passed.

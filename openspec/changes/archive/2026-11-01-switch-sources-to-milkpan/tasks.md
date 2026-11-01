# Tasks

## 1. Milkpan protocol client

- [x] 1.1 Add `src/powerspec/milkpan_client.py` (`Milkpan`, `MilkpanError`, `MilkpanUnavailable`): one subprocess per call with `--home`, `--format json`, `--protocol 1`, a deadline-aware timeout and no shell; methods `protocol`, `version`, `acquire`, `reacquire`, `release`, `lease`, `path`, `link`; verify unit tests with a stub executable (a small Python script) for success envelopes, error envelopes on stderr, exit codes, timeouts and unparsable output

## 2. Managed milkpan binary

- [x] 2.1 Add `src/powerspec/milkpan_binary.py` with the pinned `MILKPAN` release (tag v0.2.0, per-platform assets and SHA-256 from the release's `SHA256SUMS`), platform normalization, verified chunked download with a size limit, safe zip/tar extraction outside the home, and a maintainer script `scripts/pin_milkpan.py <tag>` that rewrites the pin from `SHA256SUMS`; verify tests for digest mismatch, unsupported platforms, unsafe archive members, and that every supported platform has a digest
- [x] 2.2 Implement `ensure_milkpan(home)` and `inspect_milkpan(home)`: `POWERSPEC_MILKPAN` override, compatibility check (protocol 1, version line), bootstrap, self-acquire in `powerspec-manager` with digest check, `link --name milkpan`, and repointing when the pin changes; verify tests against a loopback release fixture (built around `MILKPAN_TEST_BINARY` or skipped with a reason) for first bootstrap, reuse without download, a pin change repointing the link, a digest mismatch leaving the link unchanged, and inspect never downloading
- [x] 2.3 Generate and maintain `<home>/milkpan.toml` under `<home>/powerspec.lock` (manager rule, consumer and candidate rules with lease obligations, append-only consumer list); verify tests that a new consumer's rules exist before its first acquisition and that existing rules are preserved

## 3. Source store on milkpan

- [x] 3.1 Replace `SaucepanSources` with `MilkpanSources` in `sources.py`, keeping `for_consumer`, `lookup`, `ensure`, `acquire`, `commit`, `commit_new`, `reject`, `consumer_path`, `scope` and `SourceBinding`; recipe-to-spec mapping (GitHub, local path, `file://`, rejection of other origins); candidate-then-commit selection; `milkpan-state.json` with gitignore; sweep of unreferenced commit leases; error mapping; verify unit tests with a fake client for mapping, two-phase publication, reject, release of replaced leases only when unreferenced, and lookup never mutating
- [x] 3.2 Update callers (`workspace.py`, `upgrading.py`, `installation.py`, `cli/hook.py`, `cli/sync.py`, `cli/upgrade.py`) and progress stages (reuse versus download from `fetched`); verify the existing workspace, sync, upgrade and hook tests pass with the renamed store
- [x] 3.3 Rewrite the source integration tests (`test_sources_integration.py`, `test_source_cache_integration.py`, `test_default_bootstrap_integration.py`, `test_zmem_migration_integration.py`) to use local git repositories through milkpan's `local:` provider with a real milkpan; verify them for fresh init, repeated init reuse, two consumers sharing content and updating independently, sync without refresh, upgrade refreshing, and failed upgrade keeping the previous selection

## 4. Doctor, status and removal of Saucepan

- [x] 4.1 Update `doctoring.py` and `statusing.py` to report milkpan executable compatibility, managed link state versus the pin, and standalone overrides, without mutation; verify doctor and status tests for compatible, behind-the-pin, standalone and missing cases
- [x] 4.2 Remove `saucepan_bootstrap.py`, `saucepan_provider.py`, `saucepan_tool.py`, the `saucepan-sdk` dependency (regenerate `uv.lock`), `tests/saucepan_release_fixture.py` and Saucepan-only tests, and any remaining `saucepan` references in `src/`; verify `git grep -i saucepan -- src tests pyproject.toml` finds nothing and `uv run pytest` passes

## 5. Documentation and CI

- [x] 5.1 Update `docs/remote-sources.md`, `docs/initialization.md`, `docs/foundation.md`, `docs/context-sync.md` and the README: milkpan home and policy ownership, supported origins, the `POWERSPEC_MILKPAN` override, self-update on the next run, re-running init after the switch, and removed Saucepan variables; verify every documented command and variable exists in the code
- [x] 5.2 Make CI download and verify the pinned milkpan release for the integration tests (`POWERSPEC_MILKPAN` / `MILKPAN_TEST_BINARY`); verify the workflow runs the integration tests instead of skipping them

## Workflow follow-up

- Verify, then archive, syncing `managed-milkpan-binary`, retiring `managed-saucepan-binary`, and the `remote-sources`, `cli-product-surface` and `user-skill-installation` updates.

# Tasks

## 1. Shared standing policy checkpoint

- [x] 1.1 Add failing catalog tests, implement contained body_file normalization with existing reference handling, and pass strict validation/containment/catalog regressions.
- [x] 1.2 Wire one unconditional zmem body into persistent context and runtime traits; verify exclusions, missing tooling/source metadata, both events, and actual context publication; document shared-body authoring and fallback, then checkpoint with zmem excluding active changes.

## 2. Delivery diagnostics checkpoint

- [x] 2.1 Add failing CLI/diagnostic tests, implement doctor --agent stage checks and honest warning/failed semantics, and verify disabled/missing/malformed registrations, resolver errors, stale context, and unverified host receipt without mutations.
- [x] 2.2 Update README and hook troubleshooting with executable commands and evidence limits, run affected suites and strict OpenSpec validation, and create a verified zmem checkpoint excluding active changes.

## 3. Integrated evidence

- [x] 3.1 Verify packaged shared guidance and real resolver/doctor entrypoints in isolated consumer fixtures, inspect live local delivery diagnostics without changing host settings, and record what is verified versus unverified. Keep the bootstrap change separate.

## Verification evidence

- Shared-body checkpoint `a7dde04`: 83 focused catalog, profile, hook and publication tests passed.
- Diagnostics checkpoint: 66 focused CLI, doctor, condition, sync and command-group tests passed.
- Built a wheel and installed it into an isolated environment. The packaged shared body exists; actual installed resolver commands emitted the standing rule for both lifecycle events. The installed doctor validated publication, registrations and generation while reporting receipt/adherence as unverified. Its only failed prerequisite was Saucepan in the disposable empty home; no store was created.
- Live local doctor observed stale persistent context and an explicitly disabled Codex callback, while both resolver events generated guidance. Missing source metadata warnings remained visible. No host settings were changed, and no host receipt or agent adherence is claimed.
- Strict OpenSpec validation passed. The separate first-run bootstrap change remains untouched.

- Full regression suite: 498 passed, 4 skipped (317.47 seconds). Diagnostics checkpoint committed as `deb470c`; both checkpoint messages validated with zmem. Active change artifacts excluded from commits.


## Bootstrap wording follow-up

- [x] Clarify that applicable configured guidance can trigger native skill selection without explicit user naming; retain selected-only dynamic resolution and owning-guidance fallback limits.
- Skill validator passed. Resource and owned-bootstrap upgrade checks: 5 passed, 1 skipped (no distribution wheel in dist). Existing upgrade test verified exact revised content installation and preservation of foreign assets.
- Local checkpoint `6f5fbb6`; authored source updated, installed user copies not provisioned by this wording change.

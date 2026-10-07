# Tasks

## 1. Explicit selected-path resolution and coherent native handoff

- [x] 1.1 Replace installed-copy discovery in the skill command with explicit --path normalization for a directory, SKILL.md, or pspec.toml, preserving task-cwd consumer selection and content containment; verify with focused CLI tests for path forms, relative paths, spaces, invalid/missing locations, coexistence, locations outside native roots, and a native agent without a ZuAT discovery adapter.
- [x] 1.2 Preserve null, pending, and resolved outcomes; add canonical skill_path to JSON and explicit-path reruns, and reject positional names/--selected with migration diagnostics; verify both console entrypoints, stdout/stderr/exit behavior, Markdown/JSON equivalence, change isolation, pending rerun execution, and unchanged filesystem snapshots in tests/test_skill_cli.py.
- [x] 1.3 Retire the now-unused runtime installed-discovery bridge and replace its tests with native-selection boundary checks while retaining provisioning's ZuAT calls; verify existing installation/provisioning tests still enforce ownership and selected-copy write conflicts, and prove runtime resolution does not call native discovery or acquire unrelated remote sources.
- [x] 1.4 Update the ordinary bootstrap helper, bundled dynamic entrypoints, builtin profile, inert former bootstrap trait, and remaining blanket-bootstrap clauses together; update README, skill-resolution/hook documentation, the TDD example, and affected resource expectations. Verify native direct dynamic invocation reaches --path without recursion, ordinary skills need no resolver call, and focused resource/CLI/trait tests pass before treating this group as a checkpoint.

## 2. Manifest classification and generated configuration headings

- [x] 2.1 Extend explicit-reference compilation with ordered name retention and feature-owned manifest classification using the existing catalog and manifest validator; verify dynamic, ordinary, input-only, inactive-addition, absent/unreadable/malformed/escaping manifest, repeated-resource, conflicting-classification, and no-recursive-substitution cases in tests/test_conditions.py without evaluating inputs or reading branch content.
- [x] 2.2 Render one targeted heading and handoff per eligible context contribution, preserving authored bodies and provenance; verify context, artifact rules, and operation guidance through isolated sync tests, including mixed/repeated mentions, unmentioned skills, false conditions, handwritten YAML preservation, changed classification, stale-heading removal, failure atomicity, and byte-idempotent repeat sync.
- [x] 2.3 Update context-sync documentation and configuration examples with the generated headings and explicit native handoff; verify examples against actual fixture output and run the focused condition/sync tests before completing this checkpoint.

## 3. Runtime trait annotation with bounded remote evidence

- [x] 3.1 Add read-only classification evidence for deferred remote selectors after trait eligibility, validating declared names for exact and wildcard selections and deduplicating work within a dispatch; verify inactive/no-reference traits cause no lookup, missing names after complete inspection fail, conflicting known metadata fails, and no acquisition, refresh, native lookup, or persistent cache is introduced.
- [x] 3.2 Distinguish operational metadata unavailability from authored errors and thread the shared one-second metadata budget through read-only source calls and executable probes using existing timeout-capable interfaces; verify bounded stalled subprocess behavior, remaining-budget propagation, no retries, unknown fallback on missing services/materializations, and unchanged lifecycle caller defaults with focused source/hook tests.
- [x] 3.3 Apply shared dynamic headings and separate unknown-metadata headings to runtime messages, keeping diagnostics on stderr and preserving independent eligible guidance; verify real hook JSON output, mixed known/unknown references, fresh later callbacks, authored-error atomicity, supported lifecycle mappings, the unchanged five-second native handler limit, and open-stdin completion in tests/test_hooks.py and tests/test_hook_input.py.
- [x] 3.4 Document runtime classification, unknown fallback, and the absence of universal pre-skill lookup in docs/hook-delivery.md and related examples; verify those examples against fixture output and run the focused hook/source/condition tests before completing this checkpoint.

## 4. Distribution and cross-boundary verification

- [x] 4.1 Build a wheel with uv build --wheel and inspect/install it in an isolated environment; verify both console scripts implement the explicit-path protocol, packaged profiles/traits/skills carry the revised guidance, and initialization/upgrade fixtures replace old safely managed guidance without touching unrelated native assets or the real user installation.
- [x] 4.2 Run an integrated fixture from managed config publication and native hook delivery through selected-path resolution, including ordinary openspec-explore, a dynamic skill, duplicate native copies, unavailable remote metadata, a pending answer followed by a rerun, and repeated sync; verify the intended invocation chain and record any native agent walkthrough separately from automated output checks.
- [x] 4.3 Run the complete pytest suite once after focused checkpoints pass, then openspec validate annotate-dynamic-skill-references --strict and the project-wide specification validation; verify all five proposal capabilities have deltas and all required artifacts exist. Record actual validation outcomes and remaining limitations before marking the implementation complete.


## Verification record — 2026-10-07

- All 14 implementation tasks are complete. The proposal, design, tasks, metadata, and all five capability deltas are present.
- Final full regression: `uv run pytest -q -rs --basetemp=C:/pspec-tests-20261007-f81c` — **444 passed, 11 skipped** in 187.19 seconds. Nine skips require Windows symlink privileges; two require `SAUCEPAN_TEST_BINARY`. Canonical manifest containment also has a passing platform-independent regression check.
- The initial default-temp full run had 442 passing tests, 11 skips, and one failure in the unchanged installed workset transfer test. Its staging filename reached 272 characters and failed with a missing-path error despite an existing parent. The test passed with a short temp root; the subsequent full run above passed. No unrelated workset or atomic-write code was changed. One additional hook-budget test was added before the final full run.
- Focused checkpoints covered explicit-path CLI outcomes, configuration publication and idempotence, manifest-only classification, remote declared-name evidence, a real stalled subprocess, remaining-budget propagation, no retries, native hook envelopes/open stdin, pending-answer reruns, and lifecycle ownership preservation.
- `uv build --wheel` produced `dist/powerspec-0.1.2-py3-none-any.whl`. A fresh temporary virtual environment imported Powerspec from its installed wheel, verified both console scripts (pending, answered, explicit selected path, migration errors), and passed 25 packaged-resource/integration/initialization/upgrade tests. After the final manifest-validation adjustment, the wheel was rebuilt and reinstalled; 43 classification/resource checks passed against it.
- `openspec validate annotate-dynamic-skill-references --strict` passed. `openspec validate --all --strict` passed all 16 items; its long-requirement notices are informational. `git diff --check` passed.
- The complete automated handoff fixture covers configuration sync, native JSON delivery, ordinary openspec-explore, a dynamic skill, duplicate native copies, unavailable remote metadata, pending answers, explicit change reruns, and repeated sync. No native-agent adherence walkthrough was performed for this revision; automated delivery and content assembly do not establish agent execution.
- The installed pspec-tdd helper was unavailable at task start. Direct test-first checks were used without claiming that helper was resolved. Existing general utilities and the public SDK timeout API were reused; no new portable utility or dependency was introduced.
- At the implementation verification checkpoint, no real user skill installation had been upgraded and archival/commit were still pending. The authorized archive completion is recorded below.

## Commit checkpoint

One coherent commit keeps the breaking command migration, generated guidance, bundled entrypoints, documentation, and tests together:

`feat(skills): annotate dynamic references after native selection`

The final message passed `zmem check --file --deep` with no diagnostics. It cancels the superseded ZuAT installed-copy lookup decision at `6639cb2` entry 1 and records two replacement DECISION entries: native ownership of skill selection while retaining null/error/pending outcomes, and manifest-derived targeted reminders to keep ordinary skills on the native path. These changes form one coherent commit because the command migration and delivered guidance must agree.

## Archive completion — 2026-10-07

- Synced all five capability deltas into their main specifications and verified every changed requirement against its delta. Existing purpose sections and unrelated requirements/scenarios were preserved.
- `openspec validate --specs --strict` passed all 15 main specifications.
- Archived this spec-driven change after confirming all artifacts and all 14 tasks were complete.
- Ran `uv run pspec state clear --change annotate-dynamic-skill-references` after archival. It reported unchanged; no change-scoped temporary values required removal.
- No global skill installation was upgraded. The implementation, synced specs, and completed archive are included in the same commit.

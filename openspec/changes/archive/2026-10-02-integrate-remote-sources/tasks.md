# Tasks

Prerequisites: establish-profile-consumer-resolution and bundle-resources-and-initialize (transitively skill resolution). Trait hooks are independent. This change owns acquisition/catalog integration and the explicit upgrade operation contract, not a complete source-management CLI family. Specify final CLI syntax/readiness before exposing an implemented upgrade command.

## 0. CLI placeholder

- [x] 0.1 Add cli/upgrade.py using the shared unavailable handler, register it with both aliases, and extend existing public CLI tests for help, syntax, honest failure, and unchanged project/agent state. Observed missing-command red followed by 36 passing checks with uv run pytest tests/test_cli.py -q; no domain upgrade behavior implemented.

## 1. Saucepan acquisition boundary

- [x] 1.1 Pin and exercise the supported saucepan public acquisition interface in temporary state; verify repository/revision materialization and diagnostics against a controlled source, without relying on an obsolete workspace API. Pinned the Python SDK at 4e22ad00722b7d6511f83d8b89bbbd9aa3f3caff and passed the opt-in real CLI acceptance test against Saucepan 0.6.0 using an isolated registered app and Git repository.
- [x] 1.2 Add the acquisition adapter retaining repository, revision, and managed location provenance; verify fetch failures do not report success or alter an existing valid binding and document full-repository acquisition before selection. SaucepanSources now separates read-only lookup from explicit refresh and retains app, origin, requested/resolved revision, canonical source, artifact, and managed-root provenance.

## 2. Source discovery and registration

- [x] 2.1 Discover reusable .pspec catalogs within acquired sources, excluding private consumers; verify nested catalogs, boundaries, absent/invalid catalogs, and duplicate identities. Keep direct Git-path skill selection separate from reusable catalog registration.
- [x] 2.2 Connect validated external registration to the existing catalog boundary; verify builtin is reserved, missing reusable catalog content cancels the attempted binding, failed replacements preserve valid bindings, and registration performs no skill installation.
- [x] 2.3 Document explicit source acquisition/registration and provenance using working integration examples; document sync reuse and explicit upgrade separately, without implying a source add/update/remove CLI family or automatic refresh.

- [x] 2.4 Parse @gitsource/<source-identity>/<path-pattern> profile skill references and resolve identities through Saucepan's existing registration/materialization adapter; verify no inferred URLs, unknown-identity diagnostics, inert parsing/composition, and no sources/ resource type or descriptor files. Select direct skill roots, immediate * matches, or explicitly recursive ** matches; verify zmem's no-.pspec layout, deterministic expansion, complete resources, empty matches, malformed/duplicate names, source/symlink containment, and no synthetic checkout writes. Document the authored wildcard profile and selection independent of runtime doctor gating.

## 3. Selection and provisioning integration

- [x] 3.1 Resolve qualified remote skills by declared SKILL.md name through profile composition; verify different folder names, harmless unselected same-name sources, same-target selected conflicts, and distinct user/project targets.
- [x] 3.2 Pass selected complete remote resources and provenance to the existing ZuAT provisioning path; verify installed names remain unprefixed, inactive branch resources survive, and target scope/agent are preserved.
- [x] 3.3 Resolve an installed remote fixture with the real skill command while acquisition is unavailable; verify no fetch/update/repair occurs and bundled OpenSpec initialization remains independent of remote sources.
- [x] 3.4 Run relevant acquisition/catalog/provisioning integration tests with uv run pytest and openspec validate integrate-remote-sources --strict; record evidence using temporary source state and agent homes. The full suite passed 220 tests with one opt-in Saucepan acceptance skipped; the real Saucepan 0.6.0 acceptance passed separately against the pinned SDK and disposable Git/store roots. Strict change validation passed.


## 4. Explicit upgrade and removal safety

- [x] 4.1 Reuse Saucepan materialization lookup for sync and refresh only through explicit upgrade; verify sync performs no refresh/install/removal, reports missing required resources, and still reconciles obsolete managed YAML guidance normally.
- [x] 4.2 Implement validated upgrade replacement selection and managed-target removal planning using existing source/installation provenance; verify successful disappearance, last wildcard match removal, explicit source deregistration, unknown/unavailable source errors, malformed replacements, and preservation of unrelated or still-required installed copies. Saucepan exposes no deregistration evidence, so a missing app is correctly treated as unavailable and preserves copies rather than inferring intentional deletion.
- [x] 4.3 Verify supported ZuAT recoverable removal/finalization capabilities before integrating deletion. Commit removals only after every requested refresh, validation, collision check, and provisioning step succeeds; inject late source/provisioning and removal-finalization failures and prove no partially committed removals remain. If the supported interface cannot uphold this guarantee, diagnose it and preserve installed copies. One multi-asset uninstall operation owns the final boundary; failed uninstall/finalization restores its complete before-state through ZuAT before failure is reported.
- [x] 4.4 Document and test the whole-request success boundary without claiming rollback of source caches or all non-removal updates; run relevant integration tests with uv run pytest and strict OpenSpec validation. Full suite: 220 passed, one opt-in acceptance skipped; real Saucepan acceptance passed separately; strict validation passed.


## 5. Correct the Saucepan consumer boundary

- [x] 5.1 Add profile-owned Git source recipes, effective-graph conflict validation, and recipe-aware lazy catalog resolution.
- [x] 5.2 Replace per-alias Saucepan applications with one lazily registered `powerspec` application; make init acquire missing recipes, sync read only, and upgrade refresh selected recipes.
- [x] 5.3 Add exact-recipe matching with local path canonicalization and verify clean-store init, reuse, refresh, and full-root selection against the real Saucepan 0.5 CLI.
- [x] 5.4 Reconcile authored documentation, run the full suite and package builds, validate affected OpenSpec changes strictly, and exercise the current repository lifecycle. Final suite: 265 passed and one opt-in test skipped; wheel and sdist builds succeeded; both affected changes validate strictly. The real Saucepan 0.5 clean-store acceptance passed, current init acquired both declared repositories through the shared app, sync completed unchanged without acquisition, and pspec-tdd resolved as installed content. Native provisioning honestly reported pre-existing unowned skill conflicts rather than overwriting them.

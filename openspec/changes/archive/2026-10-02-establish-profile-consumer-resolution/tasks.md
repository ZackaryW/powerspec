# Tasks

Prerequisite: the completed scaffold-typer-cli change. This change adds domain libraries and fixture verification; all CLI domain commands remain placeholders.

The utility planning pass in design.md defines portable helpers separately from Powerspec application services. Each helper checkpoint includes its own verification; application policy and integration are checked in the later sections. Source classification, foundation libraries, and fixture verification are complete. Downstream command integration remains outside this change. The upgrade placeholder requires no new helper.

## 0. Portable helpers before application integration

- [x] 0.1 Implement bounded ancestor-file discovery under utils/discovery.py; verify nearest match, inclusive boundary, missing/error distinction, invalid paths, and canonical/symlink containment with domain-neutral filesystem fixtures.
- [x] 0.2 Implement deterministic dependency traversal under utils/dependencies.py; verify dependency-first order, diamond/repeated-root deduplication, missing nodes, cycle-path errors, and stable ordering without profile-specific policy.
- [x] 0.3 Implement named mapping overlays with winning origins under utils/layers.py; verify shallow replacement, native values, explicit null, input preservation, and duplicate-layer-name errors. Keep selection of layers and same-priority conflicts in Powerspec callers.
- [x] 0.4 Implement run_json_object under utils/processes.py using subprocess and json; verify argv/cwd/environment forwarding, caller-supplied timeout, exit errors, and object-only JSON using real isolated processes. Keep the five-second condition policy and readiness interpretation in its application adapter.

## 1. Catalog identity and composition

- [x] 1.1 Parse builtin/local catalogs and qualified profile, context, trait, and skill references with provenance; verify declared skill names resolve independently of folder names and duplicate names within one source fail.
- [x] 1.2 Implement profile contexts/traits/skills/vars, one user/project scope (default user), global mounting, and qualified exclusions; verify globals mount once, explicit select-plus-exclude fails, contributor scopes survive composition, and invalid/per-skill scopes fail.
- [x] 1.3 Resolve default layers and installation target descriptors; verify same-precedence conflicts, identical repeats, same-target deduplication, selected same-name collisions, harmless unselected names, and distinct user/project targets without performing an install.
- [x] 1.4 Document source/private-consumer boundaries, reserved builtin identity, and composition examples; verify the examples through the catalog/composition fixtures and show exclusions do not remove installed resources.
- [x] 1.5 Use the verified dependency helper for recursive profiles references, keeping exclusions and selected/global tier policy in composition; verify missing references, direct/indirect cycles with chain diagnostics, diamond deduplication, declaring-profile scope preservation, selected/global reachability tiers, and parent/child same-tier default conflicts independent of traversal order. Document subprofile composition using utils-planning-aware.
- [x] 1.6 Apply consumer/root-profile exclusions through subprofile composition; verify excluded-root errors, pruned child-only contributions, shared descendants retained through another path, and nested/global profiles introducing no additional exclusion layer.

- [x] 1.7 Replace manual structural validation with strict Pydantic v2 models; verify aliases, unknown fields, no coercion, typed declaration defaults/choices, and open variable maps. Keep graph/precedence/condition policy outside models.
- [x] 1.8 Bundle the mature-package-inspection trait with utils-planning-aware and strengthen its skill with proportional package/API fit assessment; validate the skill and real catalog composition without activating workflows or installing packages.

## 2. Consumer discovery and variable layers

- [x] 2.1 Implement nearest owning consumer discovery using the verified bounded-file helper, with Git/OpenSpec ownership rules in the application caller; verify nested consumers, invocations inside OpenSpec, worktree .git files, missing consumers, malformed nearest files, and no sibling/home/parent-repository fallback.
- [x] 2.2 Parse persistent config and optional temporary current shared/change tables, order their mappings under Powerspec precedence, and use the verified overlay helper to retain winning provenance; verify all seven precedence levels, explicit and omitted change selectors, missing tables, malformed present files, and isolation between two changes.
- [x] 2.3 Document direct [_change.<name>] keys and persistent versus gitignored temporal state; verify fixture snapshots prove resolution creates no files or cleanup, and two consumers sharing resource defaults retain distinct values.

## 3. Context and trait contracts with reviewed resources

- [x] 3.1 Parse contexts/ and traits/ as distinct kinds selected by profile contexts/traits lists; verify kind-scoped identity, mixed destination/compiletime shapes and legacy mode fields fail with migration diagnostics, profiles own no destinations/selectors, and composition neither compiles nor dispatches guidance. Document the evaluation-time boundary.
- [x] 3.2 Resolve typed non-interactive compile-time declarations with choices/defaults; verify config shared > selected > global > declaration, no current/change runtime participation, invalid supplied values fail without fallback, and missing utility_path never prompts.
- [x] 3.3 Move the authored Python CLI resource to contexts/ and change its profile reference to contexts; verify parsed content and defaults are unchanged from the previous resource.
- [x] 3.4 Wire the migrated Python CLI source into catalog/composition fixtures; verify defaults remain Python/Typer/uv/pytest/uv run pytest, utility_path remains explicit, test_command is not auto-derived, and the effective bundle includes TDD without BDD or automatic workflow execution.
- [x] 3.5 Move utility-plan/utility-apply to contexts/, remove their former mode fields, and change utils-planning-aware to reference them through contexts; verify parsed attachment content is preserved and old files are absent.
- [x] 3.6 Validate the migrated utility subprofile through real composition; verify Python CLI receives both skills with TDD deduplicated, planning/task guidance and apply ordering retain their distinct destinations, environmental work is excluded, and no implementation or config.yaml publication occurs during composition. Source guidance, category migration, and composition verification are complete.

- [x] 3.7 Parse optional Python when strings on context attachments/runtime trait bodies and validate expression syntax without execution; verify malformed/non-string expressions, legacy check tables/maps with migration diagnostics, and ordinary text remaining data. Document the separate unchanged skill-manifest guard contract.
- [x] 3.8 Pin compatible zuu case18 and implement its adapter with which/git_root/vars/run_json, empty builtins, and direct-dunder guarding; verify strict Boolean results, name/callback errors, short-circuit order, variable keys not shadowing capabilities, worktree roots, fresh bindings/results, and compile-time/runtime variable layers using stubs.
- [x] 3.9 Bind the verified generic run_json_object helper as the Powerspec run_json capability with the invocation environment and fixed five-second timeout; verify no shell, invocation cwd/environment, five-second timeout, valid object JSON, ok=false data, and diagnostics for invalid argv/missing executable/nonzero exit/timeout/invalid or non-object JSON with controlled subprocess fixtures. Document process exit versus readiness.
- [x] 3.10 Verify false omits only its contribution, composition executes none, and errors never become false or successful partial output; document sync snapshot/hook timing, marker versus health, and trusted host capabilities/no evaluator isolation or rollback. Do not migrate CodeGraph/zmem bundles or broaden skill guards.

- [x] 3.11 Bind armed(kind, reference) to the effective selection snapshot using existing kind-qualified identities; verify all four kinds, exact remote identities, global/subprofile exclusions and retained shared descendants, absent references without acquisition, invalid-query diagnostics, selection versus activation/installation, self/mutual queries without recursion, variable non-shadowing, and fresh snapshots. Document include/exclude examples without selection mutation.

## 4. Foundation milestone

- [x] 4.1 Run the focused catalog/consumer/context/trait tests with uv run pytest plus existing CLI regression checks; verify no placeholder becomes functional and composition and observational fixtures create no state or agent assets; isolate probe fixtures and do not claim rollback of arbitrary trusted callback effects.
- [x] 4.2 Run openspec validate establish-profile-consumer-resolution --strict and demonstrate the authored consumer resolves to the expected builtin/Python bundle and input layers; record results as the handoff to skill resolution.


## Verification record

- `uv run pytest -q`: 120 passed, including the existing CLI placeholder regressions.
- `openspec validate establish-profile-consumer-resolution --strict`: passed.
- Authored consumer demonstration read openspec/.pspec/config.toml and composed builtin, pspec-smarter-decision, utils-planning-aware, and python-simple-cli. Verified Python/Typer/uv/pytest/uv run pytest, explicit src/powerspec/utils, one TDD target, no BDD, and the package-inspection trait.
- The demonstration explicitly excluded zmem-lifecycle and adhd-friendly because their remote roots were not supplied. No consumer file was edited to add exclusions. Remote materialization/acquisition is not claimed; exact remote identity and selection behavior were verified using disposable fixtures.
- Domain code does not implement command dispatch, config publication, native event mapping, skill installation, or state cleanup. Eligible expression errors return no successful partial contribution tuple; arbitrary trusted callbacks have no rollback guarantee.

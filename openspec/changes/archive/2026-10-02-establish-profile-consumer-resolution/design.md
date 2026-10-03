# Design

## Context

See proposal.md for motivation. The CLI scaffold is implemented and archived; domain commands are placeholders. The authored builtin and Python CLI profiles, Python CLI context, consumer config, and TDD sources exist. The profile/consumer foundation is now implemented as domain libraries; CLI commands remain placeholders. The Python CLI and utility resources have moved to contexts/ and their profiles now reference contexts; TOML/content checks pass, and parser/composition verification now passes. No live installation is needed to exercise these data contracts.

This change is the foundation for implement-skill-content-resolution. Packaging, hooks, and remote acquisition consume its results later.

## Goals / Non-Goals

**Goals:** One deterministic, read-only source of effective resource references, target descriptors, and input layers for downstream operations.

**Non-Goals:** Implement any CLI domain command; install skills; publish attachments into config.yaml; evaluate runtime prompts; acquire remote sources; or implement flush/archive cleanup.

## Decisions

### Catalogs and consumer resources have distinct ownership

Root .pspec is a reusable source catalog. Private consumer resources and overrides live under openspec/.pspec and are not automatically exported or registered as external sources. The builtin identity is reserved for Powerspec resources; tests inject its catalog root rather than requiring the later packaged layout. An arbitrary repository or directory named builtin cannot acquire that identity.

Normalize validated catalog resources into identities and locations with provenance. Skills use the SKILL.md declared name, not their folder name: @builtin/pspec-tdd may locate .pspec/skills/pspec_tdd. Preserve the declared name for installation. Reject duplicate names within a source. Registering two sources with the same skill name is allowed; selecting different resources for the same agent/name/scope/project target is a conflict. Return target descriptors without writing installations.

This separates catalog composition from materialization. The remote change can supply saucepan-managed catalog roots to the same boundary without adding networking to lookup.

### Validate authored structures with Pydantic

Decode TOML with tomllib and validate profiles, contexts, traits, declarations, and persistent/temporary consumer shapes using Pydantic v2. Use strict types and forbid unknown structural fields; keep vars and direct change-variable tables open to arbitrary variable names and values. Validate declaration defaults and choices against their type and report resource/field locations. Preserve TOML aliases such as global, exclude-profiles, and _change. Identity normalization, graph conflicts, layer ordering, and Zuu conditions remain application policy. Skill-manifest validation belongs to its later change.

This replaces custom structural type checking with a mature package's supported model APIs. Pydantic adds a dependency, but supplies field diagnostics and strict nested validation; a generic validation helper in utils would duplicate those mechanics. Keep Powerspec-specific models outside utils. The four portable helpers retain their independent contracts.

### Profiles reference and compose

Keep separate string lists for contexts, traits, and skills, profile [vars], global = true, and one scope = user or project (default user) per profile. No per-skill scope objects. Compose each profile once and preserve each contributor's scope. Global discovery uses configured catalogs only. Qualified exclude-profiles entries apply before contributions; explicitly selecting an excluded profile is an error.

A selected profile's defaults outrank globals. Unequal same-precedence values are conflicts; identical repeats are harmless. Deduplicate installation contributions by resolved resource identity, agent, scope, and project root. Exclusion only changes the effective consumer bundle, never native availability.

Profiles may reference other profiles through a top-level profiles list of qualified strings. This is composition, not copying or a new installation scope. Resolve references recursively, report missing profiles and cycles with the reference chain, and contribute each resolved profile once even through repeated or diamond references. Each profile retains its own scope and resource provenance. The declaring parent does not change a child's scope.

Keep the existing two profile-default tiers: profiles reached from the consumer's selected profile contribute to the selected tier; those reached only from automatic globals contribute to the global tier. If an identity is reached through both, it contributes once at the selected tier. Parent/child depth and list order do not create additional override priorities; unequal defaults within a tier remain conflicts. Explicit consumer variables remain the way to override those defaults.

Apply the consumer's and explicitly selected root profile's qualified exclusions before expanding contributions. An explicitly selected root that is excluded is a conflict. An excluded subprofile is skipped along with contributions reachable only through it; a shared descendant reached through another non-excluded path remains eligible. Subprofiles and automatic globals do not add another exclusion layer; their exclude-profiles settings apply when they are explicitly selected as a root. Repeated references cannot restore an excluded profile.

The authored python-simple-cli profile references @builtin/utils-planning-aware through profiles. That reusable profile declares user scope, references utility-plan and utility-apply contexts, and supplies pspec-plan-utilities and pspec-tdd. Python CLI retains its direct TDD reference for its broader behavior guidance; the duplicate same-target TDD contribution resolves once. The utility profile declares no Python-specific defaults, so other bundles can compose it. It also selects the mature-package-inspection runtime trait, guarded by selection of pspec-plan-utilities. The reminder applies during relevant utility planning and does not start a workflow or install packages. The planning skill checks existing helpers, standard-library/dependency APIs, and relevant mature third-party packages; record concrete contract fit before direct reuse, adaptation, or custom implementation.

The utility-plan context attaches planning instructions to rules.design and task ordering to rules.tasks. the utility-apply context attaches to operations.apply.guidance and requires verified utility contracts before dependent wiring, followed by integration verification. Skills keep their bounded procedures; the contexts own these OpenSpec destinations and ordering. No schema artifact is added and change creation does not execute implementation. These are authored source contracts for future sync; this foundation composes and validates them without publishing config.yaml.

Alternatives rejected: copying profiles into consumers, source-order conflict resolution, and letting a global profile change another profile's installation scope. Each obscures ownership or changes behavior implicitly.

### Reviewed governance bundle direction

The agreed follow-up bundles are a global pspec-smarter-decision profile, a global repository-investigation profile, and a global zmem lifecycle profile using the external ZackaryW/zmem skills source. Completion/evidence procedures remain folded into the existing skills rather than a separate bundle. These globals retain ordinary explicit profile exclusions and do not authorize automatic skill execution.

Static repository descriptions and utility ordering are contexts. Mutable tool readiness and zmem service-doctor gating are runtime concerns. The repository-investigation skill will let the agent assess CodeGraph/Ripwire availability and task fit at use time; its trait only delivers the generic reminder. The zmem readiness condition must inspect the JSON ok field rather than equate a successful process exit with readiness. The accepted gate requires ok=true only; do not additionally require healthy. The smarter-decision and zmem bundles are now authored, with checkpoint context owned by zmem-lifecycle and skills selected through @gitsource/zmem/skills/*. Their authored presence is not evidence of implemented mounting, hooks, source registration, or installation. The expression adapter supplies command/JSON probing through run_json; production source acquisition remains follow-up work. The add-repository-investigation-bundle change combines investigation and prototype feasibility after classification and bootstrap delivery. It consumes the shared armed checker; other historical bundles are not migrated automatically.

### Python framework boundary for Zuu reuse

Zuu reuse guidance belongs to a reusable Python framework profile that Python project profiles can compose. It is not an unconditional global policy and does not belong to the language-neutral repository-investigation bundle. The framework profile will contribute compile-time reuse context: inspect relevant public Zuu cases before creating equivalent Python helpers, verify their actual contracts, and keep application policy in callers. Scope the context to the effective Python configuration; do not infer a framework dependency solely from a Python file or install Zuu just because guidance is selected. This is a follow-up authoring boundary, not an authored profile or completed migration. The generic utility-planning skill remains portable across languages.

### Consumer discovery is bounded

Walk from invocation cwd toward the enclosing Git root, supporting worktree .git files. Select the nearest owning openspec/.pspec/config.toml, including when cwd is already within that consumer's OpenSpec subtree. A malformed nearest consumer is an error. Do not fall back to siblings, an installed skill home, a source authoring checkout, or a parent repository outside the boundary. No consumer means no project layers; the skill caller may still resolve defaults or return pending.

Use one discovery result for all downstream consumers rather than duplicating a slightly different search in skill and hook commands.

### Shared/change variables preserve explicit scope

Both files have [vars] and direct [_change.<name>] keys. Config is persistent; current is temporary and later initialization establishes its ignore rule. Runtime precedence is:

1. current matching change
2. current shared vars
3. config matching change
4. config shared vars
5. selected-profile defaults
6. global-profile defaults
7. skill value defaults supplied by the caller

Use matching change tables only with an explicit selector; missing tables add no layer. Preserve winning provenance. Structural parsing and layer selection happen here; validation against a skill's input declarations and pending questions belong to skill resolution. No implicit active-change inference or state mutation.

The recorded future cleanup boundary remains: successful archive calls scoped flush to remove only that change's current table; shared/other-change values and config survive. Explicit global flush clears only shared temporary vars. Failed/cancelled archive does not flush. This is preserved design context, not an implemented or acceptance-tested requirement of these five changes.

### Resource kind owns evaluation timing

Use catalogs' contexts/ for compile-time guidance and traits/ for runtime guidance. Profiles select them through contexts and traits lists, with skills and vars unchanged. Resolve qualified references within the kind selected by the list and retain kind in identity/provenance. This replaces config/hook modes; no mode field or implicit shape-based compatibility alias remains.

Contexts carry attach destinations, optional compiletime declarations, and per-attachment when conditions. Traits carry hooks/body and an optional top-level when expression. Reject destination mixing, compiletime fields on runtime traits, and obsolete mode fields with migration diagnostics. Profiles select resources but own neither their destinations nor selectors. Skills remain procedures and retain their independent runtime manifests; they are not converted into traits.

Context compiletime inputs retain id/type/optional choices/default, with no prompt parsers. Precedence is consumer config shared vars, selected-profile defaults, global-profile defaults, declaration default. Neither current nor change-specific runtime values compile into shared config.yaml. Invalid supplied values fail without fallback. Provide value resolution as a library; publication belongs to implement-context-sync.

Preserve Python CLI defaults: Python, Typer, uv, pytest, uv run pytest. utility_path is explicit and test_command is not auto-derived. Move its resource and utility-plan/utility-apply to .pspec/contexts, remove former mode fields, and change profile references to contexts. Preserve their existing attachment bodies and utility-before-wiring ordering. User/project scope still governs skill installation only.

Alternative rejected: retaining a generic trait type with two modes. It obscures which resources are compiled snapshots and which observe runtime conditions, the boundary this revision explicitly establishes.

### Python conditions replace a separate check language

Use an optional when string on context attachments and on the top-level runtime trait. Omission is unconditional. Each string is one Python expression whose result must have type bool, without truthiness coercion. Ordinary and/or/not, comparisons, subscripting, and method calls replace check IDs/tables and extra custom condition fields. Reject legacy [[check]] declarations and check-ID maps with migration diagnostics; never evaluate bodies/defaults or ordinary TOML strings as code.

Skill pspec.toml equality-map input/dynamic guards and typed hint detectors retain their separate contract. This decision applies only to context/trait guidance conditions.

Use RestrictedExecutor.evaluate() from zuu.case18 with no automatic builtins and block_dunder_names=True. Do not use execute(), raw eval/exec in Powerspec, or maintain another expression grammar. Validate string shape and Python expression syntax during catalog parsing without executing it. Names/calls resolve at evaluation; use the resource/attachment location as diagnostic filename. Pin a compatible release or revision containing case18 when implementing. Inspected API: zuu commit 731be142933d05fe06697c17c1083c4ea2fb5f12, [case18 documentation](https://github.com/ZackaryW/zuu/blob/731be142933d05fe06697c17c1083c4ea2fb5f12/docs/case18/README.md).

Alternative rejected: extending command-exists/directory-exists check tables for each new readiness observation when Python already expresses the combinations.

### Explicit capabilities preserve input ownership

Each call receives five bindings:

- which(name): platform executable discovery in the invocation environment; return its path or None without launching it.
- git_root: the enclosing invocation Git root as a pathlib Path, including worktrees. Never borrow a catalog/installed skill root; diagnose an unavailable required base.
- vars: a fresh read-only mapping. Contexts receive persistent shared/profile values plus resolved declaration defaults, excluding current/change tables. Traits receive runtime layers and matching change layers only with an explicit caller selector, without resolving skill inputs or prompting.
- run_json(argv): a Powerspec-owned command helper, not a zuu API.
- armed(kind, reference): a read-only query over the completed effective bundle, described below.

Keep variable keys inside vars so they cannot shadow capability functions. No import or shell builtin is exposed implicitly. Copies isolate namespaces, not nested objects/callbacks.

run_json accepts a nonempty list of strings, runs argv without a shell in the invocation cwd/environment, and uses a five-second subprocess timeout. Require exit zero and stdout parsed as a JSON object. Invalid argv, missing executable, nonzero exit, timeout, invalid JSON, and non-object JSON are errors with resource/probe diagnostics. A valid object with ok=false remains data; exit zero alone is not readiness. No per-check command fields or prompting.

Runtime examples, not automatically migrated resources:

~~~toml
hooks = ["sessionStart", "afterCompaction"]
when = "which('codegraph') is not None and (git_root / '.codegraph').is_dir()"
body = "CodeGraph is a candidate for broad system investigation; assess task scope and usable alternatives before choosing it."
~~~

~~~toml
hooks = ["sessionStart"]
when = "which('zmem') is not None and run_json(['zmem', 'service', 'doctor']).get('ok') is True"
body = "Use the selected zmem lifecycle skills when their workflow is requested."
~~~

A context attachment can declare when = "vars['language'] == 'python'". Python short-circuiting skips the zmem probe when the executable is absent. Directory presence is a marker, not index health. The accepted zmem condition tests ok without imposing an additional healthy requirement.

### Query selected resources without evaluating their guidance

armed(kind, reference) returns an actual Boolean for one exact qualified resource identity in the effective bundle after composition, exclusions, and deduplication. kind is one of skill, trait, context, or profile. Profile membership includes retained globals and subprofiles; shared descendants retained by another path remain armed. Each kind has its own identity namespace. Skill names use their canonical declared identity, independent of installation folder names; resolved remote selector contributions retain concrete source-relative identities so exact remote references can be queried too. Queries use the foundation/remote adapter's existing identity normalization, not another alias registry.

Selection is the definition of armed. A trait with a false when or an unmatched event remains armed if selected. A context omitted during compilation remains armed. A selected skill need not be installed, successfully resolved, or running. This stable snapshot makes self/mutual queries ordinary membership tests rather than circular activation evaluation. A query never evaluates the referenced resource or tests its readiness.

A syntactically valid exact identity absent from the snapshot returns false, including an unselected or unavailable optional source. It does not acquire a source or probe the filesystem. Invalid kind, malformed/unqualified reference, wildcard query, or wrong argument types produce contribution diagnostics. Failures building the selected bundle remain composition errors, not an empty snapshot that makes all queries false. No consumer gives no consumer-selected resources; existing caller no-consumer behavior remains unchanged.

Bind the snapshot to one invocation and share it across its evaluations; rebuild it on subsequent sync/hook calls. Variable keys cannot replace armed. Python and/or/not express include/exclude guidance without adding inclusion tables or changing profile composition. For example:

~~~toml
when = "armed('skill', '@builtin/pspec-tdd') and not armed('profile', '@builtin/repository-investigation')"
~~~

This includes that attachment/body only under the stated selections. It neither arms resources nor disables installations or generic hooks. Context checks become compiled snapshots; runtime trait checks observe the current bundle at each eligible callback. Mutable runtime state is not compiled into a context.

Alternative rejected: defining armed as delivered, running, or condition-true. Those meanings introduce circular dependencies and confuse resource selection with downstream readiness.

### Evaluate only at the owning boundary

Composition retains validated expressions without observing the environment. Expose an injected evaluator for sync/hook callers. Evaluate each eligible contribution once with fresh bindings; preserve Python call order and short-circuiting without implicit probe caching. Do not persist results or reuse them across calls.

Sync evaluates contexts while compiling; published config.yaml remains a snapshot until another sync. Hooks evaluate event-matched, non-excluded traits on every invocation. False omits only that contribution, not other guidance, selected skills, or registrations. Syntax/name errors, direct-dunder rejection, unavailable required context, callback errors, and non-Boolean results are diagnostics, not false or permission to bypass resolution. Callers complete evaluation before publication/delivery and return no successful partial payload on eligible errors.

### Conditions are trusted executable rules

Case18 restricts names; it is not a security sandbox even with dunder filtering. Path objects and callbacks grant host capabilities, and Python introspection can bypass simple name restrictions. Expressions can mutate reachable objects or perform side effects. There are no evaluator CPU/memory/time limits or rollback; the helper timeout limits only its subprocess.

Treat selected builtin/local/remote conditions as trusted rules and author them observationally. Document this source-execution contract without inventing a trust switch or approval subsystem. Powerspec plumbing does not install resources, persist results, or prompt, but cannot guarantee arbitrary authored code is read-only or undo callback effects. Verify with stubs and disposable fixtures. Consumer discovery/content-path containment still bound Powerspec-owned operations; they do not confine native Path methods or command behavior exposed to expressions.

Alternative rejected: claiming isolation from empty builtins or dunder filtering. Untrusted execution needs a separate isolation design.

### Utility planning pass: portable helpers

Utilities under src/powerspec/utils should offer mechanics another project can use with its own data and policy. Catalog parsing, profile composition, consumer ownership, and context/trait rules remain Powerspec application responsibilities. The current change needs the following four helpers. These contracts are implemented and verified as independent helper checkpoints.

#### 1. Find the nearest file within a boundary

Proposed home: utils/discovery.py. Contract: find_ancestor_file(start, relative_path, *, boundary) -> Path | None.

Search from the supplied directory upward, including the boundary, and return the first matching file. Require start to be within boundary and relative_path to be relative and contained. Check canonical paths so an escaping symlink cannot produce an out-of-bound result. Return None when no file exists; surface permission and other inspection failures instead of treating them as absence. Read filesystem metadata only; do not open/parse the matching file or change process cwd.

Powerspec supplies its Git boundary and configuration path after handling its OpenSpec-subtree ownership rule. A formatter could use the same helper to find its nearest configuration. The helper knows neither Git nor OpenSpec. pathlib supplies path operations, but the bounded search and explicit missing/error behavior form the reusable contract.

Verification: nested matches, boundary inclusion, no match, invalid boundary/path, unreadable candidates, and escaping symlinks in temporary filesystem fixtures. A malformed configuration belongs to caller tests because discovery does not parse content.

#### 2. Traverse dependencies deterministically

Proposed home: utils/dependencies.py. Contract: dependency_order(roots, dependencies) -> tuple of node identifiers. dependencies maps each identifier to an ordered sequence of identifiers.

Return each reachable node once in dependency-first order, respecting supplied root/edge order for otherwise independent nodes. Detect missing nodes and cycles, reporting the offending identifier or cycle path. Complete validation before returning a result. This is a pure operation over caller-supplied data.

Powerspec uses it after applying profile exclusions to the graph. A build tool could use it to order tasks, or a plugin host to order dependencies. Global mounting, exclusion rules, selected/global reachability, and default precedence remain caller policy. No fitting existing helper was identified in the project or the inspected zuu results; avoid adding a graph framework for this bounded operation.

Verification: independent roots, chains, diamonds, repeated roots, missing nodes, direct/indirect cycles, and stable ordering using ordinary string identifiers. Profile-specific reachability and exclusions require separate application tests.

#### 3. Merge named value layers with origins

Proposed home: utils/layers.py. Contract: overlay_layers(layers) -> (values, origins), where layers is an ordered sequence of uniquely named mappings and origins maps each resulting key to its winning layer name.

Later mappings replace earlier values at the top level. Preserve values without string conversion or recursive merging. Do not mutate inputs; results are shallow copies, so nested values retain their normal object semantics. Reject duplicate layer names that would make origins ambiguous. The caller orders layers and checks conflicts between inputs that have equal application priority.

Powerspec supplies its selected variable layers. Another CLI could combine factory, user, and invocation settings and explain where a value came from. The helper has no knowledge of current.toml, changes, profiles, defaults, prompts, or persistence.

Inspected zuu.case8.LayeredMapping already provides shallow layering, but its added layers use JSON/assignment strings, its values must be JSON-compatible, and it does not expose winning origins. Those gaps justify this small mapping helper; do not serialize native values merely to route them through that API.

Verification: overwrites and origins, absent versus explicit null values, nested-value replacement, duplicate names, input preservation, and non-JSON native values. Test Powerspec's seven runtime layers and compile-time exclusions separately in application code.

#### 4. Execute a command and read a JSON object

Proposed home: utils/processes.py. Contract: run_json_object(argv, *, cwd, env, timeout) -> dict[str, object].

Require a nonempty sequence of string arguments, run without a shell using the supplied cwd/environment/timeout, require exit zero, and decode stdout as a JSON object. Report invalid arguments, process launch errors, nonzero exit, timeout, malformed JSON, and a non-object result distinctly. No retry, caching, printing, or implicit environment mutation. The invoked program can have effects; the helper cannot undo them.

Powerspec's condition adapter supplies the agreed five-second timeout and invocation environment. A service health checker or deployment tool could call the same helper with a different command and timeout. The helper does not interpret ok or healthy and does not know which application condition triggered it.

Reuse subprocess.run and json.loads directly inside this helper. Their composition adds the reusable process-to-object error contract; no process manager or new command language is needed.

Verification: real isolated subprocesses for a valid object, literal arguments, cwd/environment forwarding, nonzero exit, timeout, malformed JSON, and scalar/list JSON. Separately verify the Powerspec condition binding's timeout choice, diagnostics, short-circuiting, and readiness interpretation.

#### Application integration and checkpoints

Implement each helper with its focused tests before its callers. Then application modules load catalogs, select the nearest consumer, apply profile graph policy, order variable layers, validate declarations, and bind conditions. Those modules can be shared internally without being classified as generic utilities. Keep their domain records and rules outside utils.

Call tomllib directly for TOML decoding and Pydantic v2 for strict authored models. Reuse zuu.case18.RestrictedExecutor.evaluate for expressions; strict Boolean results, Powerspec binding names, and context/runtime timing belong to the condition adapter. Saucepan and ZuAT retain their acquisition and installation ownership. The CLI's existing not_implemented handler already serves the upgrade scaffold and needs no new helper.

The consumer supplies utility_path = src/powerspec/utils and the selected profile supplies Python/Typer/uv/pytest/uv run pytest. Use focused uv run pytest selectors for each helper checkpoint, then application fixtures for profile exclusions, consumer/change isolation, and the reviewed resource bundle. Migrate the three compile-time resources from their legacy trait layout as already planned before using them as valid foundation fixtures. Passing helper tests alone does not complete that migration or prove application behavior.

This pass was authored before implementation and followed manually while command resolution was unavailable. Its helper and application contracts are now implemented and verified; it does not establish package publication, automatic mounting, or command readiness. The remaining installation, skill-content, hook, sync, and upgrade operations stay in their owning changes.

## Risks / Trade-offs

- Native install policy could leak into composition ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾Ãƒâ€šÃ‚Â¢ return scope descriptors and conflicts only; the agent owns runtime installed-copy selection.
- Same-name private and reusable resources could become silently interchangeable ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾Ãƒâ€šÃ‚Â¢ preserve origin and diagnose ambiguity rather than inventing precedence.
- Premature packaging dependency ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾Ãƒâ€šÃ‚Â¢ injected builtin/local fixture catalogs establish the contract first.
- Trusted expressions can use host capabilities or run indefinitely ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾Ãƒâ€šÃ‚Â¢ document case18 limits and use explicit bindings/stub fixtures; helper timeout does not isolate the evaluator.

## Migration Plan

Add parsing, discovery, composition, and focused fixture tests without changing CLI placeholder behavior. Move the authored Python CLI and utility guidance into contexts and update their profile references and document effective layers. No user files need automatic conversion or installation. Reverting this implementation leaves authored resources intact.

Completion requires deterministic fixture results across nested consumers, worktrees, explicit changes, exclusions, conflicts, and compile-time/runtime separation. Downstream skill work starts after this foundation is implemented.

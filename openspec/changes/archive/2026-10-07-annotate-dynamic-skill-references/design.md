# Design

## Context

See `proposal.md` for the motivation and the five capability deltas for observable behavior.

The existing implementation already separates most of the needed responsibilities:

- `conditions._compile_body` recognizes authored `<skill:name>` tokens and substitutes plain names. Both context attachments and runtime traits call it. `Contribution` preserves each attachment's destination and provenance; `syncing.reconcile` publishes the complete managed text while preserving handwritten YAML.
- Catalog skill resources retain their declared name and `SKILL.md` path. `skills.load_manifest` validates version 2 without resolving inputs or reading selected branch content. `skills.resolve_skill` already accepts a root path and assembles a document using invocation-local consumer values.
- `cli.skill` currently calls `installed_skill`, which delegates to ZuAT before assembly. `tests/test_installed.py` and `test_selected_path_resolves_codex_coexistence` intentionally enforce that old discovery contract.
- Hook dispatch defers remote skills during profile composition, then renders matched, condition-eligible traits. Existing tests permit exact and wildcard deferred mentions without acquisition. Consequently, absence from `bundle.skills` does not prove an ordinary skill or an invalid name.
- The global builtin profile selects `skill-bootstrap`, and several other traits repeat its universal lookup instruction. Replacing only the CLI or the bootstrap skill would leave those delivered instructions inconsistent.

The revised native-selection boundary intentionally supersedes the older installed-discovery contract recorded in zmem `6639cb2` entry 1. It preserves the earlier ownership decision in `4e39c99` entry 3: the agent selects the skill. The command migration and operational unknown fallback below are the proposed policies for this implementation plan, not previously confirmed user answers.

## Goals / Non-Goals

**Goals:**

- Attach dynamic-resolution information to the same block as the skill reference, consistently across compile-time configuration and runtime messages.
- Classify manifest support without evaluating runtime inputs; resolve dynamic content only after the agent supplies its native-selected location.
- Preserve deterministic managed output, pending-answer semantics, and independent hook guidance during operational metadata failures.
- Make the transition complete across runtime code, bundled guidance, documentation, and package delivery.

**Non-Goals:**

- No native discovery adapter, new installation precedence, source registry, persistent classification cache, or acquisition during hook dispatch.
- No changes to manifest version 2 composition, condition syntax, profile default precedence, installation ownership, or OpenSpec YAML keys.
- No scanning arbitrary prose or handwritten config.yaml entries for skill names. Classification applies to authored `<skill:name>` references in emitted Powerspec contributions.
- No automatic editing of remote upstream skill files or execution of any skill during classification.

## Decisions

### 1. Classify references before discarding their identities

Extend reference compilation so the original authored tokens produce an ordered, deduplicated set of referenced names alongside the substituted body. Variable replacement remains single-pass: a variable whose value resembles a skill token does not create a new dependency.

Classify the selected catalog resources backing each referenced name. A readable, valid `pspec.toml` means dynamic-resolution support even if it has no `[[dynamic]]` entries or no currently active additions. No manifest means ordinary. Reuse `load_manifest` without calling input resolution, reading branch content, or evaluating runtime conditions. Canonicalize and contain the manifest within the catalog skill root; a broken or unreadable existing entry is an error, not evidence of absence.

Deduplicate the same resource selected through several profiles. When multiple selected resources have the same declared name, matching classifications can share the name-level reminder; conflicting classifications are a configuration error. This compares catalog evidence only and never decides native precedence. Invocation-local memoization is sufficient; later syncs and callbacks re-read current metadata.

This replaces manually maintained dynamic flags, which could drift from manifests, and avoids using current branch activation as a classification test.

### 2. Prepend one generated section per contribution

For a block with known dynamic references, prepend:

```markdown
### Skills requiring dynamic resolution: pspec-tdd

When the guidance below calls for these skills, select each through your native skill integration. Before following its procedure, run `pspec resolve skill --path "<selected-skill-location>" --agent <current-agent>` from the task directory. Include `--change <name>` only for an explicitly active change. Follow returned content or pending-choice instructions; report errors without bypassing resolution.
```

Keep the authored body below that preamble. Multiple dynamic names appear once in first-mention order. Ordinary names remain in the body and are excluded from the heading. The reminder is conditional on the original task trigger and does not itself activate a workflow. Already-authored headings remain intact; the generated heading introduces the reminder, not a rewrite of the author's section structure.

Configuration reminders live inside the existing managed scalar/list text, retaining the attachment identifier. `syncing.reconcile` therefore removes stale reminders and preserves user content using its current ownership mechanism. Do not add a YAML key, global inventory, or second tracking file. Each attachment remains self-contained even if another attachment mentions the same skill.

### 3. Runtime remote metadata is a bounded optional inspection

Keep initial hook composition deferred. After event matching and condition evaluation, collect references from eligible bodies. Use bundled/local catalog evidence immediately. For references that require deferred remote evidence, inspect selected remote selectors through the existing read-only catalog/source boundary. Exact selectors and wildcard selectors must be checked against declared skill names; a basename or wildcard alone is not proof of a match. No references means no metadata inspection. Deduplicate selector and source work across messages within this dispatch.

If deferred selectors could also supply the referenced name, include their evidence before declaring the classification complete. Failed inspection does not establish that the source lacks a matching skill. Successfully inspected selectors containing no match contribute absence; all complete evidence with no matching resource is an authored-reference error. Known conflicting classifications and readable malformed manifests are also authored errors.

Represent dynamic, ordinary, and unknown separately. Unknown is limited to operational inability to inspect deferred remote metadata, including missing services/materializations and timeout. Emit a separate diagnostic and a local heading such as:
Confirmed dynamic evidence remains sufficient to require a handoff when another selector is unavailable. Without that positive evidence, incomplete inspection cannot establish ordinary behavior or name absence; those references remain unknown. Conflicting known evidence still fails.

```markdown
### Skill metadata unavailable: remote-helper

Select this skill through your native integration. Check the selected copy for pspec.toml; if present, request its Powerspec content using the selected path before following the procedure. Otherwise follow its ordinary instructions.
```

Known dynamic and unknown lists remain separate in a mixed message. Preserve the body and independent eligible contributions. Never label unknown as ordinary, ask Powerspec to discover installed copies, or repair the source. Authored errors retain atomic failure; do not catch every `ConfigurationError` and convert it into unknown. Introduce a feature-owned operational error/result distinction at the source inspection boundary where necessary.

Allocate at most one second of additional remote-inspection time per dispatch, including executable probes, source calls, and successive selectors. Pass remaining time to blocking subprocess-backed operations and stop further inspection when exhausted; do not retry. The installed Saucepan SDK exposes public `Saucepan(..., timeout=...)`, retained by `for_app`, for `view`, `history`, and `path`. Existing `inspect_executable(..., timeout=...)` supports bounded executable probes. Thread this optional budget through Powerspec's read-only source adapter and executable inspection, keeping lifecycle callers' existing defaults. Source operations that share the budget must receive the remaining duration rather than a new full allowance. Use public SDK construction/calls; do not mutate its private options. Existing five-second native handler limits and condition-probe limits remain unchanged. Local filesystem behavior is subject to the existing native handler bound.

This approach uses current available evidence without requiring sync as a startup prerequisite or introducing a persisted index. The cost is that unavailable metadata produces an explicit check for the agent to perform on its selected copy.

### 4. Supply the selected location as the runtime input

The canonical command becomes:

```text
pspec resolve skill --path "<selected-directory-or-SKILL.md-or-pspec.toml>" --agent <current-agent> [--change <name>] [--json]
```

Normalize the explicit location to a canonical skill directory. Require its ordinary `SKILL.md` and valid declared name, using the existing frontmatter/name rules. Accept only a directory, its `SKILL.md`, or its `pspec.toml`; arbitrary filenames fail. Resolve relative paths from process cwd without changing it. Keep manifest and content containment checks. A valid root without a manifest returns literal null, allowing an explicit call or a stale catalog annotation to defer to the selected ordinary copy. An unreadable existing manifest or invalid path is an error.

Remove the runtime call to `installed_skill` and retire that bridge when it has no callers. Leave provisioning's direct ZuAT calls intact. `--agent` remains required for profile/invocation context but does not validate native installation membership or require a discovery adapter for that host.

Retain `skills.resolve_skill`, configuration precedence, content assembly, and existing output envelopes. Add canonical `skill_path` to resolved and pending JSON; derive `skill` from selected frontmatter. Render pending reruns with `--path` and preserved selectors. The paths in generated guidance are placeholders for native selection, never embedded catalog-source paths.

Reject positional names and the former `--selected` spelling with a clear migration diagnostic and empty stdout. A parser compatibility shim may recognize these forms solely to explain the replacement; it must not discover or resolve anything. This ends the old discovery behavior immediately instead of maintaining two selection authorities. Genuine relative paths use explicit `--path`, removing ambiguity with old names. Valid form failures remain exit 1; CLI syntax failures retain Typer's nonzero usage behavior.

### 5. Retire universal delivery coherently

Remove `@builtin/skill-bootstrap` from the builtin profile's active trait list. Retain the ordinary helper skill, rewritten to explain conditional native selection and the explicit-path command. Keep the former trait identity as an inert compatibility resource (`body = ""`) so authored profiles referencing it do not fail while it can no longer reintroduce the universal instruction.

Remove blanket bootstrap clauses from the decision, repository-investigation, utility-planning, ADHD, and zmem guidance wherever they appear. Classification of their explicit references provides the correct reminder automatically. Ordinary skill procedures should directly describe native use.

Add concise direct-invocation handoff instructions to bundled manifest-backed entrypoints (`pspec-tdd` and `pspec-smarter-decision`). They must say that content already returned by Powerspec is ready to follow, preventing recursive assembly. Do not change their manifest anchors or ask the agent to manually assemble every branch. Keep entrypoints and their generated/example documents coherent.

The startup registration itself stays generic and unchanged. Package/runtime resource updates replace its delivered content. Skill installations are updated only by the existing requested lifecycle operations; this planning or implementation change does not rewrite this machine's global skill directories.

### 6. Reuse existing mechanics and verify the changed boundaries

All new logic is Powerspec policy: reference classification, reminder wording, source availability, and the explicit skill handoff. Keep it in the feature owners (`conditions.py`, `skills.py`, `hooks.py`, `sources.py`, and CLI adapters), with a small feature module only if separation improves readability. No new general-purpose utility or dependency is needed.

Reuse the existing placeholder recognizer, manifest validator, catalog/source APIs, `pathlib` normalization, YAML reconciliation, SDK timeout, and executable inspection interfaces. Do not build a new parser, package detector, installer, shell-escaping library, or concurrency framework. Test their integration at the changed public boundaries instead of manufacturing utility tasks.

Focused verification must establish:

- Reference behavior: static/dynamic/input-only/unknown, multiple names, duplicate mentions, no recursive substitution, inactive contributions, absent and malformed manifests, conflicting classification, and no branch reads.
- YAML behavior: context/rules/operations coverage, unchanged provenance, handwritten content preservation, removal and reclassification, and byte-idempotent repeated sync.
- Hook behavior: real JSON envelope, no stdin dependency, no source acquisition or native lookup, deferred exact/wildcard evidence, timeout/unknown fallback, fresh later callbacks, and authored-error atomicity.
- CLI behavior: both console scripts, path forms and spaces, coexistence, locations outside native roots, project cwd, missing/invalid paths, old syntax migration, null, pending reruns, and Markdown/JSON equivalence.
- Delivery behavior: packaged resources and updated native-installed fixtures contain no universal requirement; native direct dynamic invocation and generated reminders both reach the same content command without recursion.

## Risks / Trade-offs

- **Catalog and native versions can differ** -> Treat annotations as catalog-derived guidance; the runtime command uses only the agent's selected path and retains explicit null/error handling.
- **Remote inspection can delay startup** -> Use one bounded, invocation-local metadata budget, no acquisition, no retries, and an explicit unknown fallback. Test stalled subprocess calls rather than only immediate mocked errors.
- **Ordinary absence can be confused with inspection failure** -> Preserve a three-state classification and distinguish readable invalid metadata from operational unavailability at the source boundary.
- **Shared reference rendering affects many traits** -> Test configuration and hook integrations independently, including messages without skill tokens and unrelated optional-probe failures.
- **Old executable, bundled guidance, and installed entrypoints can be mixed** -> Ship command and resource changes together, provide migration errors, and verify supported lifecycle reconciliation in isolated installations. Do not claim existing sessions have received new instructions.

## Migration Plan

1. Implement and verify the explicit-path command and shared classification behavior before switching delivered guidance to the new command.
2. Integrate sync and hook annotations, including bounded remote inspection and unknown reporting, with focused checks for each complete slice.
3. Update bundled profiles/traits/entrypoints, README and command examples; verify a built distribution contains the new resources and both console scripts honor the new protocol.
4. Validate all change deltas and run a final regression pass across the affected shared boundaries. Do not claim native agent adherence from serializer or unit-test success; record any agent walkthrough separately.
5. Release the executable and bundled resources together. Consumers use the normal authorized lifecycle update to reconcile installations, then sync configuration. Starting or compacting a session delivers the current targeted guidance.

Rollback uses the previous executable/resources as a pair followed by ordinary installation reconciliation and sync. Manifest format, user configuration, and runtime answers are unchanged; no data migration or history rewrite is required.

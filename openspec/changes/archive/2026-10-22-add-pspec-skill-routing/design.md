# Design

## Context

See `proposal.md` for motivation and scope. The primary goal is to avoid loading many scenario-specific skills into one agent session before their scenarios apply. The user confirmed that `pspec:foo` searches only the current consumer's effective profile selections, including resolve-only selections. A matching configured rule can trigger retrieval without the user naming the skill again. The requested authored skill target is `.pspec/skills/pspec-skill-bootstrap`, not the installed copy under the user's Codex home.

This revision uses `main` at `f97b955` as its evidence baseline. The change remains planning-only.

Current evidence:

- `cli/skill.py` requires `--path`, calls `selected_skill`, and deliberately rejects positional names and `--selected`. `_bundle` composes profile defaults without materializing skills. `tests/test_skill_path.py` verifies that paths outside known native roots need no installation adapter or write.
- `models.Profile` accepts one `skills` list and one installation scope. `profiles.compose` produces `Bundle.skills` installation targets and a selection snapshot. `provisioning.plan_skills` consumes those targets; `installation.install_consumer` and `upgrading.upgrade_consumer` keep source preparation and ZuAT writes separate from runtime lookup.
- `catalog.Catalog` already resolves qualified catalog names and concrete or wildcard Git selectors, preserving declared names and remote provenance. `workspace.open_workspace` can use read-only source lookup and defer skill expansion. `upgrading._remote_refs` currently reads only profile `skills` declarations.
- `SkillReferences` derives native dynamic handoffs from installation targets and deferred selections. `conditions._compile_body` recognizes `<skill:name>` tokens, not literal `pspec:foo` text. Resolving a new delivery type must not cause resolve-only skills to be advertised as native discoveries.
- `.pspec/profiles/builtin.toml` installs the ordinary bootstrap skill but selects no bootstrap trait. `.pspec/traits/skill-bootstrap.toml` is currently inert. Existing startup and compaction dispatchers can deliver a routing reminder without new callback registrations.
- The current bootstrap already allows applicable persistent/runtime guidance to select a skill without another user mention, forbids loading all configured skills, and preserves fallbacks permitted by owning guidance. `.pspec/guidance/zmem-lifecycle.md` is shared by context and trait through `body_file`; its standing memory rule remains visible when tooling is unavailable. `guidance_doctor.py` separately observes selection, publication, registrations, generation, and unverified host receipt/adherence.
- `models.GuidanceBody` and `Catalog._resolve_bodies` now support contained shared guidance before existing reference processing. Workspace/source operations now carry scoped lifecycle progress, but protocol callers remain silent without a progress observer. Extending delivery intent must preserve these behaviors.
- `resources.builtin_catalog_root` can create a temporary merged directory for editable installs. Returning a skill path from that directory would break supporting-file access after command exit. `tests/test_resources.py` exercises this editable overlay.

Zmem `eb42c64` entry 2 records the existing native-selection boundary; entry 3 records targeted dynamic reminders. The new explicit namespace extends those decisions without restoring installed-copy discovery. The archived design at `openspec/changes/archive/2026-10-07-annotate-dynamic-skill-references/design.md` explains why a second native lookup was removed.

Current-snapshot zmem recall and origin inspection also confirm `6f5fbb6` entry 1 (bootstrap owns handoff; scenario triggers and permitted fallbacks remain with their guidance), `a7dde04` entries 1-2 (unconditional standing memory policy and shared guidance bodies), and `18dbbd6` entry 1 (progress is scoped to human lifecycle commands). These remain constraints on this extension, not behaviors to replace with a blanket resolver.

## Goals / Non-Goals

**Goals:** Keep scenario-specific skill discovery entries and procedure bodies out of the session until needed; keep bootstrap and lightweight applicable rules sufficient to retrieve one procedure; distinguish availability, native installation, and actual content retrieval; preserve native selection and existing dynamic composition, source retention, and durable supporting-file access.

**Non-Goals:** No new plugin format, native name-discovery adapter, installation precedence, per-prompt callback, automatic source acquisition during resolution, persistent extracted skill cache, or conversion of all existing builtin skills to resolve-only delivery. Do not change unrelated sync lifecycle wording or repair global installations during this work.

## Decisions

### 0. Treat profile selection as availability, not a request to load procedures

The context delivery sequence is:

```text
Session starts
  --> bootstrap discovery and lightweight scenario rules are available
  --> scenario-specific procedures remain in the Powerspec catalog

Current task matches a configured rule, or the user requests pspec:A
  --> bootstrap retrieves A
  --> only A's procedure and selected active additions enter the response
  --> B and C remain deferred until their own scenarios apply
```

For resolve-only selections, Powerspec does not add native discovery entries for each target. Bootstrap's discovery metadata and the compact routing reminder explain the access route; the bootstrap body itself need only be read when routing is needed. The existing persistent/runtime guidance owns task conditions and can contain a small rule such as `When planning a reusable helper, use pspec:@builtin/pspec-plan-utilities`. Such a rule names the scenario and target without embedding the target procedure. Bootstrap does not copy all conditions into itself or ask the user to repeat a skill name when a rule already applies.

No startup, compaction, initialization, profile composition, or status operation may be treated as permission to prefetch procedures for the agent. A resolver can inspect candidate identity metadata internally to establish membership or uniqueness; that internal work is separate from emitting skill bodies or a descriptive inventory into the conversation. Explicitly requested status and ambiguity diagnostics can still show the identities needed for their own contract.

Resolving A must not expand sibling procedures, inactive branches, or every referenced supporting document. Read additional supporting resources or retrieve another skill only when the active procedure actually needs them. Several relevant skills may be used in a session when several scenarios occur; there is no arbitrary one-skill-per-session cap or promise to unload previously consumed text.

Alternative: install every scenario helper and rely solely on its native description, or hide an eagerly fetched catalog behind bootstrap. The former still exposes each target to native discovery; the latter still places unnecessary procedure content in the session. Resolve-only availability plus scenario-triggered retrieval is the context-reduction mechanism. It takes effect for profiles authored with resolve-only targets in a fresh native setup; existing installed copies, unrelated plugin inventories, and already-loaded session text do not disappear as a side effect.

### 1. Add an explicit catalog selector to the existing protocol

Use mutually exclusive options:

```text
pspec resolve skill --path "<native-selected-location>" --agent codex
pspec resolve skill --ref "helper" --agent codex
pspec resolve skill --ref "@builtin/helper" --agent codex
pspec resolve skill --ref "tools/skills/helper" --agent codex
```

`--ref` accepts a declared skill name or an exact existing qualified resource identity. Bootstrap removes only the `pspec:` namespace prefix from the selector supplied by the user or applicable scenario guidance; it does not invent a folder or strip the `pspec-` portion of a declared name. Thus `pspec:pspec-tdd` addresses declared name `pspec-tdd`. `pspec:@builtin/pspec-tdd` can disambiguate that resource. Invocation selectors cannot contain wildcards.

Exactly one selector and an explicit invoking agent are required. Retain the legacy positional-name and `--selected` migration errors. `--path` remains authoritative even when a catalog or installed copy differs and still returns `null` for an ordinary selected directory. `--ref` requires an owning consumer and returns ordinary catalog content as well as manifest-backed content.

Alternative: revive positional-name discovery or make bare names guess between paths, native installations, and catalogs. Rejected because the route would become ambiguous and weaken the existing selection contract. A separate command is possible but would duplicate the same input/output and pending protocol without improving the namespace boundary.

### 2. Make resolution availability an additive profile declaration

Add a strict optional `resolve-skills` string list using the same qualified/catalog and direct-Git selector validation as `skills`:

```toml
scope = "user"
skills = ["@builtin/pspec-skill-bootstrap"]
resolve-skills = ["team/skills/*"]

[[source]]
id = "team"
provider = "git"
origin = "https://example.test/team/agent-tools"
reference = "main"
```

This is authored profile configuration, not a new field in the consumer's `config.toml`. The consumer selects the profile through its existing `profile` field. `resolve-skills` means available for a relevant scenario, not load all listed skills now. Authors use that list for scenario-specific targets while keeping bootstrap and any deliberately native workflows in `skills`.

Keep `Bundle.skills` as installation targets so existing ZuAT planning cannot accidentally receive resolve-only resources. Add a separate collection for resolved `resolve-skills` contributions, retaining declaring profile and source provenance without an agent installation destination. Keep the selection snapshot as the union of both declaration types, with the existing deferred-composition behavior and global/subprofile exclusions. `armed('skill', exact_ref)` reports selection in that union, not native availability.

A resource appearing in both lists remains one candidate identity for catalog lookup and keeps every explicitly requested installation target. Different resources with the same name can coexist as resolution candidates; a bare invocation must disambiguate them. Existing same-destination installation collisions still fail.

Update status additively: retain `skills` for installation selections and add `resolve_skills` for the new declarations. A resource declared in both can appear in both lists. Human labels distinguish declarations from successful installation.

Alternative: add `scope = "none"` or reinterpret `skills` as resolution-only. Rejected because installation scope and delivery intent are separate, existing profiles must keep their behavior, and composed profiles already preserve per-declaration provenance.

### 3. Select from the effective bundle using read-only catalog evidence

Put catalog selection policy in the skill feature, with the CLI limited to input validation and presentation. Start from `open_workspace` with source lookup, runtime consumer values, and deferred skill expansion. Gather both declaration lists from retained profiles rather than treating all resources in configured sources as callable.

For a bare name, expand the selected candidates with existing `Catalog.select`, match the declared `SKILL.md` name, and deduplicate by exact resource identity. Return one match; fail with exact usable references for multiple matches. If a selected source cannot be inspected, fail as incomplete evidence rather than claiming a visible candidate is unique. An unselected same-named resource does not participate.

For an exact identity, validate that it is admitted by a retained exact selection or a selected wildcard, then resolve only the relevant source and selector evidence. This preserves the useful case where an exact local skill works while an unrelated remote source is unavailable. Do not compose all remote resources eagerly just to retrieve that local skill. Membership in a wildcard is established against its actual selected resource identities, not inferred from a name or basename.

Use `SaucepanSources.lookup`, the owning consumer's retained receipt, and the manager-returned root for remote selections. No acquisition, registration, binary installation, refresh, native lookup, or variable write occurs in this route. Missing materializations direct explicit `init`; refresh remains an explicit `upgrade` action. The path route continues to avoid remote skill expansion entirely.

Alternative: search every configured source or use ZuAT's native-name lookup. Rejected because the user selected an effective-profile boundary and explicit catalog requests must not depend on native installation state.

### 4. Keep source lifecycle and provisioning intent distinct

Source preparation must validate/materialize selected remote selectors from both lists. Extend upgrade's remote-reference collection to both lists so resolve-only sources can be refreshed. Preserve the existing receipt publication and recovery boundaries.

Build installation plans only from `skills`. Compute old installed candidates, current installation targets, obsolete-copy evidence, and ZuAT removal requests only from installation contributions. Adding or removing a resolve-only declaration does not independently adopt or uninstall an existing native copy. Merely changing an authored selection from `skills` to `resolve-skills` is not historical proof authorizing native removal. Existing remote obsolescence handling remains based on verified installation evidence.

Native authored `<skill:name>` handoffs remain installation-oriented. Adjust `SkillReferences` to distinguish deferred installation declarations from the union used by `armed`; a resolve-only resource must not become a native candidate simply because it is selected. If a token names only a resolve-only resource, issue an actionable authoring error recommending literal `pspec:name`. Literal `pspec:` text in a scenario rule passes through existing body rendering without inventory expansion, dynamic classification, or execution; the agent follows it only when its owning condition applies. This avoids a second prose-scanning or placeholder language. Preserve `body_file` processing before classification and do not drop an unconditional standing rule merely because its target skill or service is unavailable.

### 5. Return durable source locations and share assembly

Expose the original complete skill root for catalog content. Remote roots already come from retained Saucepan receipts. Consumer-local roots are the configured catalog directories. For builtin skills, extend resource-origin handling so a selected skill maps to its underlying complete checkout-authored directory or installed packaged directory, not the temporary merged catalog used for metadata discovery.

Keep metadata overlay precedence explicit: a complete authored skill tree wins for that skill; packaged-only upstream skills use their installed packaged tree. Preserve the declared identity and verify that returned content and the supporting-file root are from the same selected tree. Do not reconstruct an arbitrary path from a skill name, rely on a deleted temporary directory, or silently combine files from incompatible trees. A partial authored skill that cannot supply its selected complete tree is an error requiring a complete source tree. A resource provider offering only transient extraction is explicitly unsupported for this route; normal filesystem wheel installations and complete editable skill trees are required. No new persistent extraction or native-copy fallback is introduced.

After selection, only the requested manifest-backed root goes through the existing `resolve_skill` input/assembly pipeline. Ordinary roots use the existing safe document reader with entrypoint frontmatter removal. Other candidate procedures, inactive dynamic additions, and unrelated supporting files are not returned or resolved as speculative dependencies. A malformed manifest never becomes ordinary fallback. Add concise canonical-reference/source-root metadata to the catalog Markdown result so relative supporting resources have an explicit base. JSON repeats those values as `skill_ref` and `skill_path`, and its `content` equals the full Markdown result.

Parameterize pending presentation by selector type: catalog retries use the selected concrete reference; native retries retain their exact path. Keep agent and explicit change selectors in either case. Do not write answers during lookup or return procedural content while required inputs are pending.

Alternative: hand the agent the temporary catalog root, keep the context alive indefinitely, or install a copy to stabilize it. Rejected because the first breaks references after exit, the second does not survive a CLI boundary, and the third contradicts resolve-only delivery. Underlying whole-tree origins use already-maintained sources.

### 6. Put agent routing in the requested bootstrap skill

Update `.pspec/skills/pspec-skill-bootstrap/SKILL.md` and its concise description to recognize user `pspec:` requests and catalog references selected by applicable scenario rules. Keep it ordinary and natively installed by the builtin profile. Its body distinguishes two selection routes: a needed catalog target calls `--ref`; an existing native dynamic target calls `--path` with the exact host-selected location. The owning guidance decides whether the current task requires that skill; neither the user nor bootstrap must enumerate all available skills first.

For catalog requests, follow returned resolved content without recursively following the entrypoint's assembly reminder. Use the durable source root for supporting files when needed. Obtain missing answers from pending results and retain concrete identity, cwd, agent, and explicit change on retry. For ambiguity, present the returned exact references rather than guessing. Failures remain failures without installing skills or substituting native copies. Preserve the current bootstrap's explicit distinction between bypassing an unresolved procedure and continuing a fallback already permitted by owning guidance: report the limitation, do only that permitted work, and claim neither successful skill execution nor memory verification. Retrieval does not expand task scope or authorize external actions.

Activate the existing `.pspec/traits/skill-bootstrap.toml` identity in the builtin profile. Keep a short `sessionStart`/`afterCompaction` reminder guarded by bootstrap selection, for example:

```text
When the current task needs a pspec:<skill> target named by the user or
applicable scenario guidance, use <skill:pspec-skill-bootstrap> to retrieve
that target only. Do not preload other selected skills.
```

The trait owns only discovery; the skill owns the handoff procedure; each scenario's owning guidance retains its task condition. Existing native dynamic annotations remain beside their eligible mentions. Do not add universal pre-skill resolution, a catalog inventory, procedure bodies in startup/compaction output, extra prompt/tool callbacks, or longer native deadlines. Excluding the builtin profile removes its routing reminder through ordinary selection semantics. This adds no service-readiness guard to standing guidance and preserves the branch's delivery-diagnostic distinction between generated output and actual host receipt/adherence.

### 7. Reuse application APIs without inventing utility work

Existing `Catalog.select`, resource identity/frontmatter parsing, contained shared guidance bodies, `open_workspace`, Saucepan lookup/retention, `manifest_supported`, `read_document`, `resolve_skill`, Markdown pending handling, and profile dependency traversal provide the required mechanics. The additions are Powerspec-specific policy: delivery intent, selected-catalog name matching, origin mapping, and routing text. Keep them with their feature owners; no new portable helper, third-party dependency, separate utility plan, or prototype is needed. Resource-lifetime regression checks belong at the CLI/package boundary, where they establish actual post-exit usability. Retain existing scoped progress stages for lifecycle work and keep skill/hook protocol calls silent without an observer.

### 8. Verify the context boundary across several scenarios

Use isolated profiles selecting bootstrap natively and ordinary/dynamic targets A, B, and C through `resolve-skills`, with small scenario rules and distinct procedure-body sentinels. Before any scenario, assert that the native target files/discovery entries for A/B/C were not provisioned, startup/compaction output contains the lightweight rules and routing reminder without their procedure bodies or descriptions, and no catalog procedure-resolution call occurs. Adding further unused resolve-only targets must not expand the routing reminder into an inventory.

Next exercise a configured scenario A without a user skill-name mention: the documented bootstrap command returns A's procedure and active additions only. B/C and A's inactive-branch sentinels remain absent from that response. An unrelated task or restoration of routing guidance must not prefetch B/C. When scenario B later applies, retrieve B alone; C remains deferred. Allow a real dependency explicitly required by an active procedure to be retrieved at its point of need rather than imposing a session-wide skill limit.

Verify resolver calls, emitted context, and the fresh fixture's native files, without claiming those checks prove the live model's private context or adherence. Retain explicit-user invocation, pending answers, durable roots, native-path regressions, standing-policy fallback, shared-body behavior, delivery diagnostics, and silent protocol progress checks. Implementation must satisfy these observable boundaries; installation count alone is insufficient evidence of deferred procedure loading.

## Risks / Trade-offs

- Name collisions and incomplete remote evidence can prevent a bare lookup. Exact selected references provide an explicit route; no source priority or native-scope guess is introduced.
- The CLI change reaches profile composition, status, source refresh, and handoff classification. Keep the two contribution types visible throughout these paths and prove resolve-only targets never enter ZuAT plans.
- Editable metadata overlays can hide a temporary origin or partial tree. Verify real subprocess results and supporting-file readability after exit for authored and packaged-only skills; reject unsupported transient-only roots.
- Activating the former inert trait changes its delivered context. Limit it to on-demand routing for user requests or applicable scenario rules and retain native timeout, event, exclusion, and ordinary invocation regressions.
- Existing native installations and third-party plugin inventories remain independently discoverable, and previously loaded text cannot be removed by this resolver. Measure the reduction for resolve-only selections in a fresh isolated setup; broader profile migration or cleanup needs an explicitly scoped follow-up.
- Agent adherence remains separate from hook delivery. Validate the serialized invocation chain and bootstrap contract; do not claim a live agent followed the procedure based only on an emitted reminder.

## Migration Plan

1. Add and verify the profile selection/lifecycle distinction before catalog resolution consumes it. Existing profiles need no edits and retain installation semantics.
2. Add and verify explicit catalog selection, stable origins, ordinary/dynamic results, and pending retries while retaining all path-route compatibility checks.
3. Update the authored bootstrap skill and builtin trait/profile together once the command exists, retaining the current branch's configured triggers and permitted fallbacks. Document a resolve-only profile with a lightweight scenario rule and a separate explicit-user namespace example; retain the native path example.
4. Verify the multi-scenario context boundary and complete source/built-wheel invocation chain against the updated branch. Installation or upgrades of this machine's agent assets remain separate authorized lifecycle actions, not side effects of editing or testing these resources.

Rollback restores the additive code/resources and removes `resolve-skills` declarations from consumers before running an older release, whose strict profile parser will reject the new field. Rolling back this change does not require uninstalling resolve-only targets because none were created. Do not delete source receipts or rewrite shared native assets to simulate rollback.

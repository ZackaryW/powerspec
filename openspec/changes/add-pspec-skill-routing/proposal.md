# Proposal

## Why

Scenario-specific skills should remain available without adding all their discovery entries or procedures to an agent session. Powerspec needs on-demand retrieval through a small bootstrap and lightweight scenario rules, so only the skill needed for the current task enters context; `pspec:<skill>` is the retrieval reference, not a requirement for the user to name every skill manually.

## What Changes

- Extend the ordinary bootstrap skill at `.pspec/skills/pspec-skill-bootstrap/SKILL.md` to retrieve a catalog skill when the user requests it or an applicable configured scenario rule calls for it, while preserving its existing native-selected-path handoff and owning-guidance fallbacks.
- Add profile `resolve-skills` selections for resources that are available through Powerspec but are not installation targets. Existing `skills` entries remain installation targets and are also eligible for explicit Powerspec lookup.
- Add an explicit `pspec resolve skill --ref <name-or-qualified-reference> --agent <agent>` route, mutually exclusive with `--path`. Search only the current consumer's effective profile selections after exclusions, as confirmed by the user; diagnose missing or ambiguous names.
- Return ordinary or dynamically assembled catalog skill content, stable source locations, and actionable pending/error results without installing skills, refreshing sources, or probing native installations.
- Keep bootstrap discovery and lightweight scenario rules visible; deliver only a compact startup/compaction routing reminder. Do not emit a catalog inventory, eagerly load every selected procedure, or load unrelated skills and branches when one scenario applies. Preserve the updated branch's standing guidance and native invocation; add no per-prompt or tool callbacks.
- Verify the context boundary with several selected scenario skills: startup exposes their routing rules without their procedure bodies, scenario A retrieves A alone, and B/C remain deferred until their own scenarios apply. Preserve existing profile installation behavior and native `--path` semantics; broad migration of existing profiles and changes to this machine's installed skill copies remain outside this change.

## Capabilities

### New Capabilities

None. Extend the existing profile, resolution, bootstrap, CLI, and hook capabilities.

### Modified Capabilities

- `profile-skill-bundles`: Distinguish resolve-only availability from installation targets while retaining exclusions, source validation, provenance, and selection membership.
- `cli-product-surface`: Offer explicit catalog reference resolution alongside the existing path protocol and expose resolve-only selections in status.
- `skill-content-resolution`: Return only the needed selected procedure and active branches, with stable access to supporting files and existing dynamic input semantics.
- `skill-bootstrap`: Route user requests and applicable scenario guidance to on-demand content retrieval alongside the native-selected-path route.
- `trait-hook-delivery`: Keep routing reminders and scenario rules lightweight at the existing supported lifecycle boundaries without eagerly delivering selected skill procedures.

## Impact

The primary authored skill target is `C:/Users/ZackaryW/Desktop/+workplace/powerspec/.pspec/skills/pspec-skill-bootstrap`. Supporting work affects profile models/composition, catalog selection, resource location handling, the skill CLI, status, source preparation/upgrade selection, builtin profile/trait resources, and focused tests and documentation. Reuse the existing catalog, Saucepan lookup, manifest resolver, and ZuAT installation boundary; no new dependency or plugin packaging format is planned.

This explicitly extends the native-selection decision recorded by zmem `eb42c64` entry 2: native invocation continues to honor the agent's selected copy, while the explicit `pspec:` namespace selects Powerspec catalog content. Neither route silently substitutes for the other. Planning artifacts authorize no implementation or global skill installation.

The revised plan is reconciled against `main` at `f97b955`: retain its configured bootstrap triggers and permitted fallbacks, shared contained guidance bodies, unconditional standing memory policy, guidance-delivery diagnostics, and silent resolution protocols alongside lifecycle progress. Context reduction is measured for resolve-only selections in a fresh isolated setup; this change cannot remove already-loaded session text or skills independently exposed by another native plugin.

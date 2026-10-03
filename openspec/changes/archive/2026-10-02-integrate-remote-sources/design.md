# Design

## Context

See proposal.md. Builtin/local composition and scoped installations are established by the earlier changes. No Powerspec remote adapter exists. Remote acquisition was formerly one task inside the oversized plan; it does not block the first working builtin resolver.

Prerequisites: establish-profile-consumer-resolution and bundle-resources-and-initialize, transitively including skill resolution. This can proceed independently of trait hooks.

## Goals / Non-Goals

**Goals:** Feed validated saucepan-managed catalogs into existing selection/provisioning with retained provenance and honest acquisition errors.

**Non-Goals:** A custom Git cache, implicit fetch during skill lookup, runtime OpenSpec fetching, remote push, or another skill installation manager.

## Decisions

### Saucepan materializes; Powerspec discovers; ZuAT installs

Use the verified saucepan acquisition interface behind a narrow adapter. Inspection of commit 4e22ad00722b7d6511f83d8b89bbbd9aa3f3caff found full non-shallow repository acquisition and complete revision materialization before folder filtering. Do not promise selected-file-only network transfer.

Keep source repository/revision and managed materialization identity separate from Powerspec catalog references. Discover .pspec catalogs in that materialization, validate names and resource shapes through the existing foundation, and expose source roots without copying them into builtin. Ordinary catalog discovery with no .pspec cancels its attempted catalog binding; direct @gitsource references validate selected skill paths without requiring a remote .pspec. A failed acquisition or invalid replacement preserves an existing valid binding.

Source discovery must remain within the acquired source boundary and must diagnose ambiguous declarations across discovered catalogs. Private consumer resources under openspec/.pspec remain private and are not registered as reusable external catalogs. This retains the agreed source/consumer distinction while allowing a repository to publish more than one reusable catalog.

### Git source references pair profile aliases with recipes

Profiles select skills through `@gitsource/<alias>/<path-pattern>` and declare the matching recipe with `[[source]]`. In `@gitsource/zmem/skills/*`, `zmem` is a Powerspec alias; its profile declaration supplies provider `git`, the repository origin, and requested reference. Identical declarations may be shared by composed profiles. Differing recipes for the same alias fail composition before materialization. `builtin` remains reserved. Powerspec does not derive a URL from the alias or create a `sources/` resource folder.

All selected recipes use one ordinary Saucepan application named `powerspec`. A single application can touch multiple Git sources. Init lazily initializes the Saucepan store, registers that application, and acquires a selected recipe only when no matching current materialization exists. Repeated init reuses existing content without refresh. Sync reads the same application view and never initializes, registers, or acquires. Upgrade explicitly reacquires each selected recipe. Friendly aliases remain profile composition data rather than Saucepan app names.

Resolve each recipe by matching provider, origin, and reference in the application view, then use Saucepan history and path for the current full-root artifact. Saucepan may canonicalize local paths to file URLs; equivalent local path forms compare canonically while remote URL, provider, and reference matching stays exact. Retain the alias plus Saucepan source, artifact, requested reference, resolved revision, and root provenance.

Resolve the selector within the materialized source root. A direct skill directory selects that directory; `*` selects matching immediate child directories, and recursive selection requires `**`. Candidate skill roots carry `SKILL.md`; unrelated files and non-skill directories are not installed. An empty initial selection is a diagnostic. During upgrade of an established selection, a successfully refreshed, valid source can establish an empty replacement set. Validate selected skill frontmatter and complete resources, reject duplicates and malformed selected skills, order expanded roots deterministically by source-relative path, and deduplicate identical resolved selections through the existing target contract.

Canonical source/path boundaries apply including symlinks; reject absolute or escaping selectors. Preserve external Git-source/revision/path provenance while installing each `SKILL.md` declared name unprefixed. Direct skill selection requires no remote `.pspec` and writes no synthetic catalog into the source checkout.

The authored zmem-lifecycle profile pairs `@gitsource/zmem/skills/*` with the `https://github.com/ZackaryW/zmem` `main` recipe. Its checkpoint context compiles independently of service health. The runtime trait checks doctor's JSON `ok` before supplying zmem guidance; false does not uninstall selected skills, disable checkpoints, or suppress other profiles. Acquisition and installation do not establish workflow execution or service readiness.

Alternative rejected: one Saucepan app per friendly alias. Saucepan apps represent consumers and can touch multiple sources; multiplying applications would confuse selection aliases with the consumer boundary and require out-of-band registration.

### Registration is not selection or installation

Reserve builtin before any external binding. Preserve declared SKILL.md names, even when source folders differ. A qualified reference such as @team-tools/pspec-tdd identifies provenance but still installs as pspec-tdd through ZuAT.

Do not conflict merely because an unselected source contains the same name. Use the existing selected-resource target collision check, then pass complete resources and provenance through existing provisioning. Ordinary installed lookup reads installed contents and never repairs or refreshes sources.

### Sync preserves; explicit upgrade refreshes

Sync resolves declared recipes from the existing `powerspec` Saucepan application through the same source adapter. It never refreshes a source, installs or removes skills, or interprets source unavailability as deletion. Required resources absent from existing materialization produce diagnostics without a fetch. This preserves installed skills while allowing sync's normal reconciliation of obsolete managed context guidance in config.yaml.

An explicit upgrade action refreshes the selected profile recipes through the `powerspec` Saucepan application, validates their replacement selections, and provisions selected complete skills through ZuAT. pspec upgrade is the working command name; this change establishes the operation contract without inventing a source add/update/remove command family or automatic refresh.

A successfully refreshed and validated source can confirm that a previously selected skill is absent. Explicit removal of a source registration can also identify obsolete source-backed copies. Fetch failures, inaccessible materializations, unknown identities without evidence of explicit removal, and invalid replacements are errors rather than confirmed absence. Reuse source and installation provenance; removal applies only to managed copies in the requested targets and must preserve copies still required by another effective selection or owned outside this operation.

Removal is committed only when the entire requested upgrade succeeds, across all its requested sources and targets. Finish acquisition, selection validation, collision checks, and provisioning before committing any removals. A late failure must preserve prior installed copies, including skills already identified as obsolete from another successfully refreshed source. Removal/finalization failures must not leave partially committed removals or report success. Verify recoverable removal/finalization through the supported ZuAT interface before implementing this guarantee; if that interface cannot uphold it, report the limitation and preserve copies rather than perform best-effort deletion. This does not promise rollback of Saucepan caches or every non-removal update.

### Keep the public surface bounded

Deliver source acquisition, selection/provisioning integration, and the explicit upgrade lifecycle contract. No remote push, background refresh, custom Git cache, or parallel native skill manager is introduced. Both aliases expose `upgrade --agent <agent>`, which upgrades every selected remote skill reference in the owning consumer's effective bundle. The command has no per-source selector or implicit registration behavior.

ZuAT exposes recoverable multi-asset uninstall rather than an atomic removal materializer. Submit all obsolete copies in one operation for the selected agent and consumer, verify absence as finalization, and restore the operation's complete before-state if uninstall or finalization fails. A failed restoration is reported as partial and never as success. An unavailable Powerspec application or unmatched recipe preserves installed copies rather than establishing intentional removal.

## Risks / Trade-offs

- Saucepan interfaces differ by release → pin and exercise the chosen supported public API rather than coding against an old Python workspace API.
- Full repository acquisition is more expensive than filtered resources → expose the real behavior; bundled OpenSpec remains local.
- Failed fetch/discovery could leave a misleading binding → validate materialization before replacing registration and preserve prior valid state.
- Native removal might lack recoverable finalization → verify ZuAT capabilities before implementation; preserve installed copies if the whole-upgrade removal guarantee cannot be upheld.

## Migration Plan

Add the adapter, validate discovery/registration, then connect its catalog output to profile selection and provisioning. Use controlled remote fixtures and temporary saucepan state/agent homes. Verify actual acquisition separately from pure adapter fixtures, preserve names/provenance, and prove skill lookup performs no fetch.

Builtin remote profiles gain explicit recipes. Existing compatible materializations in the Powerspec application are reused; other Saucepan applications are not rebound automatically. A failed registration does not delete unrelated cache checkouts or installations. Exercise upgrade failures after individual source refreshes, late provisioning, and removal finalization; no failure may leave committed obsolete-skill removals.

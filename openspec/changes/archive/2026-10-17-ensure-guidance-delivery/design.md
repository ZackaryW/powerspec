# Design

## Context

See proposal.md. Zmem recall confirms the valid lifecycle-only delivery decision at 95539ba entry 1 and separate compile/runtime ownership at 327c9db entry 1. Preserve both. Current doctor only probes versions; native registration and host settings are separate, and current Codex user settings contain an explicit disabled startup entry. Generating an envelope cannot prove host receipt or adherence.

## Goals / Non-Goals

Goals: durable task triggers, no duplicated instruction body, diagnostic evidence for each observable boundary, and bounded read-only verification.
Non-goals: changing host trust, per-prompt hooks, guaranteed agent compliance, receipt logging infrastructure, or the pending Saucepan bootstrap fix.

## Decisions

- Add optional `body_file` alongside inline body in strict resource models, exactly one allowed. Resolve relative to the catalog root at catalog load with the existing containment check and UTF-8 decoding. Reject traversal/absolute paths and escaping links. Normalize to body for downstream code; retain the file declaration for provenance. Contexts and traits still own separate conditions and destinations. A checked-in guidance Markdown file is included by the existing whole-catalog package rules.
- Select a zmem context and trait pointing at that file. Remove the trait's service-health condition. Authored text specifies the semantic task trigger, lookup plus corroboration, explicit unavailable-tool fallback, existing commit authority, and no execution of unrelated skills. No zmem service probe occurs merely to deliver this standing rule.
- Add optional `--agent` to doctor. Without it, preserve prerequisites and add a warning that delivery was not inspected. With it, compose without materializing skills; inspect current config.yaml for the expected rule, inspect native JSON registrations for both expected command/matcher pairs, and inspect known user settings for explicit disabling. Use CODEX_HOME for Codex and CLAUDE_CONFIG_DIR for Claude when set. Unknown host layers, trust and settings remain unverified; do not implement host hash algorithms or guess effective enablement.
- Feature-owned delivery diagnostics live in `guidance_doctor.py`. Reuse normal bundle composition, catalog access and executable inspection. Invoke the installed `pspec resolve hook ... --agent ...` with finite timeouts for each event, validate SessionStart/additionalContext, and require the standing body when its trait is selected. Preserve diagnostics from stderr. Report host receipt and adherence as warning/unverified, never infer them from exit zero. DoctorResult.ok means no failed observations, not complete verification.
- Basic/agent doctor and manual resolver tests exercise real CLI argument parsing and output. Isolated filesystem fixtures cover overrides, exclusions, malformed settings, disabled hooks, and missing sources. Native host receipt remains explicitly unverified in product output and verification reports unless a separate real-host observation exists.

### Utility assessment

Reuse pathlib, tomllib/json, Catalog._contained, inspect_executable and existing workspace APIs. No new portable helper contract or dependency is needed: body resolution belongs to catalog resource ownership, and native-settings interpretation belongs to the agent-specific diagnostic feature. Do not invent a generic hook framework or modify trusted host settings. Shared-file loading is additive; inline resources need no migration.

## Risks / Trade-offs

- Hosts merge multiple settings layers and trust definitions → only report observed local restrictions; leave overall effective activation unverified.
- Persistent context does not automatically reach ordinary conversations → retain runtime hooks and document that independent route.
- Missing selected remote metadata can warn during rendering → retain the rule and diagnostics without provisioning; malformed readable manifests still fail normally.
- `body_file` affects all catalog loading → test strict validation, both body forms, containment, reference classification, package inclusion, and existing catalog tests before integrating resources.
- Generating new persistent context may encounter existing source-readiness failures in sync → verify isolated publication, report live limitations, never silently acquire unrelated sources to satisfy a diagnostic.

# Proposal

## Why

The reviewed profiles and consumer TOML files exist, but no runtime code can resolve their identities, scopes, or variable precedence. Establish this shared foundation first so skill lookup and hook delivery can use fixture-tested inputs without waiting for packaging or network acquisition.

## What Changes

- Parse builtin/local catalogs, qualified resource identities, referenced subprofiles through a profiles list, profile defaults, global mounting, exclusions, and one installation scope per profile.
- **BREAKING** Separate compile-time contexts from runtime traits: profiles reference contexts, traits, and skills separately; catalogs use contexts/ and traits/ without a mode field. Validate non-interactive context inputs without publishing config.yaml.
- Replace the proposed custom checks with Python expression strings in when on context attachments and runtime trait bodies. Reuse zuu case18 and provide explicit environment, variable, and command-JSON capabilities; publication and event dispatch remain downstream work.
- Expose armed(kind, reference) to context/trait conditions as a read-only query of the effective bundle after exclusions; selection is independent of installation, condition success, and execution.
- Discover the nearest consumer within the invoking Git boundary and resolve persistent/temporary, shared/change variable layers.
- Align the authored Python CLI resource with its compile-time context ownership; preserve uv, pytest, and uv run pytest defaults.
- Compose the reusable utils-planning-aware profile into Python CLI, supplying separate design/task planning and apply-ordering contexts plus utility-planning and TDD skills.
- Supply reusable resolution results with provenance; perform no installation, prompting, synchronization, or cleanup.
- Plan portable file-discovery, dependency-traversal, mapping-overlay, and command-JSON helpers before integrating them into Powerspec domain services. Utility contracts must support reuse by another project.

## Capabilities

### New Capabilities

- `profile-skill-bundles`: Resource identity, recursive subprofile composition, scope, exclusions, context/trait ownership, Python guidance conditions, utility planning/apply guidance, and reviewed Python CLI defaults.
- `consumer-configuration`: Git-bounded consumer discovery and shared/change variable precedence.

### Modified Capabilities

None.

## Impact

Adds domain parsing/resolution behind the existing src/powerspec/cli scaffold, plus focused fixtures and configuration documentation. Depends only on the completed CLI scaffold. No command becomes functional in this foundation change. Skill execution, ZuAT provisioning, remote fetching, hooks, full sync, and flush remain separate.

Completion means builtin/local fixture catalogs and consumer configurations produce deterministic effective bundles and input layers with useful errors. Success does not require a live agent or a packaged distribution.

Adds a compatible zuu dependency containing case18. Conditions are trusted Python expressions with explicit bindings, strict Boolean/error outcomes, and a Powerspec-owned argv-to-JSON probe helper. Context conditions run during sync; trait conditions run at invocation. Composition executes no conditions and persists no results. This does not migrate a CodeGraph/zmem bundle or implement publication/dispatch. Exposed objects and callbacks are capabilities, not a security sandbox.

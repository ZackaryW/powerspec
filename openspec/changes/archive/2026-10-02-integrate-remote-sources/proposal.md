# Proposal

## Why

Builtin and local resources should work before networking is introduced. Add remote sources as a separate integration so saucepan acquisition can feed the same catalog and provisioning contracts without complicating ordinary skill lookup.

## What Changes

- Expose explicit `upgrade --agent <agent>` behavior through both aliases after the source and recovery contracts are implemented.
- Acquire remote sources through saucepan and discover their .pspec resources, or select skill folders directly through @gitsource/<source-identity>/<path-pattern> references.
- Declare friendly Git source aliases and exact provider recipes inside profiles, then materialize every selected recipe through one Powerspec-owned Saucepan application while preserving materialization/revision/path provenance without adding a Powerspec sources/ resource folder.
- Register validated external source identities with provenance while reserving builtin for packaged resources.
- Resolve remote qualified references by declared skill name and reuse existing profile composition and ZuAT provisioning.
- Reject invalid source bindings and surface acquisition/discovery errors without silently changing an existing binding.
- Keep read-only skill lookup and ordinary bundled OpenSpec installation independent of remote fetches. Init acquires missing selected recipes, sync reuses existing materializations, and both preserve installed skill copies on failure.
- Refresh source-backed selections through an explicit upgrade action. Remove confirmed obsolete managed skills only when the entire requested upgrade succeeds; failed or unavailable sources do not establish absence.

## Capabilities

### New Capabilities

- `remote-sources`: Explicit acquisition, validated registration, catalog or direct Git-path skill selection, and end-to-end source provenance.

### Modified Capabilities

- `cli-scaffold`: Add the no-argument upgrade placeholder to equivalent entrypoint help and syntax. Resource identity and installation conflict behavior continue to reuse profile-skill-bundles and user-skill-installation.

## Impact

Depends on establish-profile-consumer-resolution and bundle-resources-and-initialize (which in turn depends on skill resolution); does not depend on hook delivery. Adds a saucepan acquisition adapter and connects acquired catalogs to existing selection/provisioning. No custom Git downloader or native skill-management layer is added.

Completion means a controlled remote fixture is acquired, registered, selected, and provisioned with its declared name and provenance, while ordinary lookup remains read-only. This does not reintroduce upstream OpenSpec downloads during init or remote push. Upgrade owns the bounded removal of obsolete managed source-backed skills; sync remains configuration reconciliation.


The authored zmem-lifecycle global profile selects external zmem skills, builtin checkpoint context, and a runtime doctor-gated trait. Remote acquisition/install selects skills independently of runtime doctor outcomes; the trait controls guidance only. The profile uses skills = ["@gitsource/zmem/skills/*"]. This authored reference precedes implementation of the source adapter.

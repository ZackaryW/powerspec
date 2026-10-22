# Design

## Context

See proposal.md for motivation. The clean sibling zmem2 checkout is at b14d257911270565dcb6228da435520ef79cf506 and declares package zmem2 0.1.0, command zmem and Node 24/26 support. Node 26 is available. Its built CLI exposes init, sync, recall and file/stdin checks. All three installed Codex skill directories match this checkout byte-for-byte.

Powerspec owns declarative profile resources and Saucepan selections, not a zmem service client. The bundled profile still points at the predecessor repository. Source state is keyed by the full recipe, so an origin change requires a new selection. Upgrade composes existing selections through lookup before refreshing; initialization is therefore the migration entry point. ZuAT already reuses matching skills, updates intact owned skills and refuses local edits.

Two predecessor zmem.exe launchers are visible on PATH: a uv-managed tool and a second file under the user's .local/bin. The old user home contains db/runtime/service files but no shared config.yaml. The new engine uses versioned v2 user storage and environment-scoped repository indexes. No legacy database conversion is needed.

## Goals / Non-Goals

**Goals:** Align selected source, installed skills and executable; make the authorized machine usable for computed queries and commit checks; preserve old data and explicit rollback information.

**Non-Goals:** Add an automatic runtime installer to pspec init, port Python extensions, change hook registrations, clean old retained sources, introduce a service health prerequisite, publish a release, or push commits.

## Decisions

1. Keep the source alias, main reference, profile and native skill identities. Change only the origin and clarify the shared guidance's runtime contract. Renaming them would break exclusions and native discovery without solving runtime selection. Retain ordinary provider freshness and consumer pin semantics.
2. Use the upstream package/build contract and existing package managers for the local switch. Test a packaged build from the clean known revision in an isolated prefix/home before selecting it globally. Inventory both legacy launchers and preserve hashes, installation metadata and rollback copies before removing shadowing commands. Prefer package-manager removal for its owned tool; preserve a separately installed launcher outside PATH. Verify both a new PowerShell process and subprocess resolution, rather than relying on npm install success.
3. Preserve the default user home and predecessor db/runtime files; the new engine writes its separate v2 storage. Preserve existing configuration if discovered. Initialize Powerspec using the selected new engine, track its minimal repository configuration and nested ignore file, and keep generated indexes ignored. Use bounded, no-background verification calls for initial acceptance and report actual coverage rather than claim a full-history audit.
4. Migrate existing consumers with the updated Powerspec installation and init --agent codex, then sync guidance. New-origin preparation does not need force merely to escape the predecessor's cache. Keep ownership checks; do not use blanket skill overwrite or delete source receipts. An installation failure must retain prior selections and recovery evidence. Document conflicts as explicit repair work under the existing contracts.
5. Reuse Saucepan, ZuAT, npm/uv and the existing composition/provisioning owners. No reusable helper or new Python API is required; the utility-planning rule does not introduce work here. Focus tests on actual bundle selection, delivered guidance, changed-origin acquisition and preserved native ownership.

## Risks / Trade-offs

- Same command name and multiple launchers can keep selecting Python -> inventory resolution, preserve rollback files and verify the resolved command from fresh shells and subprocesses.
- Main can advance independently of the installed runtime -> retain package revision/hash evidence and require runtime command-surface verification in the skill/guidance contract.
- Source change leaves no new-recipe selection for lookup-first upgrade -> initialize first and test that migration path.
- Existing native edits can conflict with migration -> preserve them and surface the existing ZuAT diagnostic; do not infer overwrite authority from a source URL change.
- Bounded initial memory omits older history -> report attention and memory coverage; verification is not a complete historical audit.
- Old service files can be live -> do not delete or rewrite legacy databases, runtime directories, configuration or extensions.

## Migration Plan

First verify the packaged new CLI independently. Record predecessor installation and data inventory, install the new package, retire only confirmed shadowing launchers, and verify normal command resolution. Initialize repository memory and validate a focused checkpoint with the selected engine. Then apply and test the bundled-resource/documentation change, rebuild the installed Powerspec tool, initialize the consumer's new source and reconcile skills, and sync persistent guidance. Finish with relevant tests, full pytest, strict change validation and recorded acceptance evidence.

Rollback uses the recorded predecessor package source and preserved separate launcher, together with unchanged legacy data. Restore the previous Powerspec package/profile and its retained recipe if needed. Do not erase the new index or old data to simulate rollback. Archive and main-spec synchronization remain separate requested workflows.

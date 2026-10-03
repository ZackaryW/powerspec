## Context

See proposal.md for the deployment failure and lifecycle correction. The application already separates consumer file creation, source ensure/lookup/refresh, and ZuAT provisioning. The regression is in orchestration, plus first-use error classification. Existing CLI and context-sync specs conflict with the older initialization provisioning spec; the deltas resolve that conflict explicitly.

## Goals / Non-Goals

Restore the approved command flow with existing services. Preserve revision reuse, user files, profile scopes, and partial-failure reporting. Do not add an agent detection system, credential fallback, dependency framework, automatic upgrade, or new utility abstraction.

## Decisions

- Add optional --agent to init. Validate a supplied agent before file effects. Plain init prepares sources without provisioning an unidentified agent; init with an agent reuses install_consumer internally. Keeping the internal installation service avoids duplicating ZuAT policy while removing its public command.
- Scaffold before source composition. A later acquisition/provisioning failure leaves the configured consumer and completed assets intact for retry. Report this explicitly, with no all-or-nothing claim. This replaces the inconsistent earlier promise to validate the full bundle before writing on a fresh consumer.
- Resolve init's setup against its Git-root consumer, including when invoked below a nested consumer. Sync continues using the nearest consumer.
- Sync uses ensure instead of lookup. Ensure reuses a matching current materialization and only acquires absent recipes. Upgrade retains its existing refresh and deferred-removal policy. Compilation and YAML publication still wait for complete composition; source acquisitions are separate persistent effects.
- Recognize both missing-secret and missing-index errors, then use Saucepan.init. Saucepan owns its native key and existing-store guards. Do not infer that missing secret proves an empty store, and never repair by deleting existing data.
- Remove install from root registration and delete its command module. Move its reporting to init. Update current docs and bootstrap resource; archived artifacts stay unchanged.

## Risks / Trade-offs

- First sync can need network access -> report acquisition failures and preserve YAML; repeated sync reuses revisions.
- Setup can partially complete -> retain successful assets and describe rerunning init with the same agent.
- Native credentials are machine-specific -> unit regressions cover reported missing-secret behavior; real CLI acceptance uses isolated test stores and does not claim testing the other computer's credential service.
- Existing install scripts break -> docs and help identify init --agent as the replacement.

## Migration Plan

Ship code, bundled guidance, and docs together. Existing consumers need no file-format migration. Rerun init --agent for agent setup and sync for configuration. Existing materializations are retained. Verify entrypoints from a built wheel in addition to focused source tests.

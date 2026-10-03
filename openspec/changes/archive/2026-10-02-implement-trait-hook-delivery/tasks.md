# Tasks

Prerequisites: establish-profile-consumer-resolution, implement-skill-content-resolution, and bundle-resources-and-initialize. Remote sources do not block this change.

## 1. Verified native event contracts

- [x] 1.1 Verify selected target hosts' sessionStart and afterCompaction callback identities, incoming context, and response formats; record pinned host/ZuAT evidence distinguishing command execution from actual guidance delivery, and report unsupported mappings.
- [x] 1.2 Implement logical/native selectors and per-trait exclusions after positive expansion; verify one excluded callback does not suppress other traits, other callbacks, or generic registrations, including the no-contribution case.
- [x] 1.3 Document only verified native spellings and capabilities; verify examples do not present the illustrative ~claude:postcompaction spelling as a supported API without evidence.

## 2. Trait dispatch and bootstrap resource

- [x] 2.1 Implement hook.py with adapter-supplied agent/native-event/cwd context and shared nearest-consumer discovery; verify two consumers, nested/worktree boundaries, missing consumer/no match, malformed nearest config, and no executable-location fallback.
- [x] 2.2 Dispatch only matching runtime trait bodies using native response serialization; verify context attachments are excluded, no unrelated prompts/skill execution/state writes occur, and failures do not masquerade as delivered guidance.
- [x] 2.3 Author the unconditional skill-bootstrap runtime trait with sessionStart and afterCompaction and reference it from builtin alongside pspec-skill-bootstrap; verify TOML shape, reference, and bounded reminder text.
- [x] 2.4 Verify through composition/dispatch that profile exclusion removes only this contribution and the delivered reminder identifies the installed bootstrap skill without activating other workflows.
- [x] 2.5 Update hook help/readiness and document consumer-specific dispatch; verify pspec/powerspec aliases and the remaining sync/flush placeholder contracts.
- [x] 2.6 Evaluate eligible trait Python when expressions through the shared adapter with event cwd/environment/Git root and effective runtime vars; verify executable/marker combinations, worktrees, short-circuiting, per-trait false omission, excluded events never evaluated, explicit change layers only, and freshness without sync or registration updates.
- [x] 2.7 Verify syntax/name/non-Boolean/probe failures yield diagnostics without successful partial guidance, variables cannot shadow capabilities, no results persist, and run_json distinguishes ok=false from execution/JSON failure; use stubs/controlled probes in disposable fixtures. Document trusted effects/no isolation or rollback, preserving unguarded bootstrap and marker-versus-health distinctions.

- [x] 2.8 Forward the invoking consumer's effective bundle to armed; verify selection after exclusions, false-condition/unmatched-event membership, no query recursion or installation lookup, and freshness across two callbacks without changing generic registrations.

## 3. Generic user-level registrations

- [x] 3.1 Generate and provision generic callbacks through the existing explicit-agent ZuAT adapter during init; verify user scope regardless of profile skill scope, native context forwarding, and absence of baked-in consumer bodies.
- [x] 3.2 Verify repeat provisioning reuses callbacks, preserves unrelated settings, reports modified/unmanaged conflicts and partial failures, and leaves registration intact when all trait contributions are excluded.
- [x] 3.3 Document supported mapping/install/recovery behavior and verify native context delivery in isolated settings separately from the dispatcher process merely exiting successfully.

## 4. Bootstrap delivery milestone

- [x] 4.1 Run an isolated session-start and post-compaction walkthrough covering ordinary null fallback, pending/answered TDD, and broken manifest; record delivery separately from agent adherence and workflow execution.
- [x] 4.2 Verify an environment-only session receives bootstrap guidance without TDD/BDD activation or input questions, then run relevant tests with uv run pytest and openspec validate implement-trait-hook-delivery --strict.

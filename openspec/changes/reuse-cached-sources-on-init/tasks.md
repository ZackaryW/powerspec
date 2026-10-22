# Tasks

## 1. Bounded shared retrieval policy

- [x] 1.1 Add the 86400-second retrieval-refresh override to ordinary missing-selection preparation using manager profile expansion; verify focused source tests cover returned catalog consumption, unchanged retained-pin lookup, explicit refresh policies, and pending-intent reuse across retries.
- [x] 1.2 Extend real-manager source integration tests with two isolated consumers, a shared store and local Git origin; use Git traces and test-only provider clock injection to verify cold retrieval, warm reuse, the 86399/86400-second boundary, future-dated evidence, offline behavior, and independent pins. Run the focused integration suite with the pinned Saucepan binary.
- [x] 1.3 Document the bounded policy and unchanged existing-selection semantics in docs/remote-sources.md; verify documentation matches tested ordinary init and explicit upgrade behavior, then review this complete policy checkpoint before dependent work.

## 2. Explicit provider recovery boundaries

- [x] 2.1 Extend the existing manager adapter with default-off migration authorization and observed-digest arguments to the pinned verified official installer; verify disposable installer/provider fixtures cover successful migration with matching backup hash, changed-file rejection, unsupported candidates, ready-manager reuse, standalone bypass, and no work without source demand. Document eligibility and backup handling with this checkpoint.
- [x] 2.2 Preserve original provider operation identities after pending, conflicting or uncertain migration outcomes, including when the launcher is unavailable; verify repeated forced requests do not blindly replay migration or create replacement identities, and document recovery instructions without deleting backups or provider receipts.
- [x] 2.3 Thread default-off hook receipt-repair authorization through agent installation using existing ZuAT guarded repair; verify source-matching stale receipts repair without native byte/mtime changes, edited or ambiguous hooks fail, concurrent content changes are rejected, unrelated hooks survive, and operation identifiers remain available. Document these bounded effects.

## 3. Forced init integration and progress

- [ ] 3.1 Add init --force and wire explicit source refresh, migration consent, and agent-scoped hook repair as separate internal intents; verify CLI-entrypoint tests cover with/without agent, missing/existing source selections, invalid-agent early failure, success publication, later-failure reporting, and conflicting pending ordinary/refresh intent.
- [ ] 3.2 Verify force does not authorize skill overwrite, manager self-update, obsolete-skill removal, ambiguous hook replacement or provider-guard bypass; verify ordinary init remains non-migrating/non-repairing and upgrade retains its current force and repair-hooks semantics. Update CLI help and examples to enumerate all init force effects.
- [ ] 3.3 Report validated retained reuse, cache-eligible preparation, explicit refresh, migration and guarded hook repair through existing progress observation; verify stderr/stdout separation, provider operation identifiers, silent library calls, failure/heartbeat cleanup, and absence of unsupported cache-hit or transfer claims. Update progress examples and review this complete integration checkpoint.

## 4. Integrated acceptance

- [ ] 4.1 Run the relevant source, CLI, managed-provider, installation, hook, upgrade and progress tests followed by the complete pytest suite once; repeat isolated cold/warm/second-consumer/forced-init smoke experiments with Git tracing and record observed operations/revisions without timing thresholds or mutations to the user's ready installation.
- [ ] 4.2 Validate this change with openspec validate reuse-cached-sources-on-init --strict and review implementation against all three delta specs; record provider-side materialization costs separately and prepare focused local commit checkpoints using session commit-authoring rules when authorized.

## Workflow follow-up

- Apply after the revised planning artifacts have been reviewed and implementation requested.
- Archive and sync only when requested after implementation and verification; do not push.

# Design

## Context

See proposal.md for motivation and measured baseline. `SaucepanSources.ensure` already returns a validated retained pin for an existing consumer selection. A new consumer reaches `_policies(False)` and `prepare_group`; the manager's `explicit-update` profile expands to cached storage but always-refresh retrieval. Separate consumer scopes correctly isolate selections and must remain separate.

The installed and pinned provider supports `refresh_policy` with `max_age`, `always`, and `cache_only`. Its maximum-age comparison accepts only nonnegative ages strictly below the limit. The SDK exposes `profile(..., catalog=..., retrieval_policy_refs=..., acquisition_policy_refs=...)`. These existing APIs cover the change. Current init has no force option; upgrade's force option controls skill replacement.

## Goals / Non-Goals

**Goals:** Change retrieval freshness without creating a second cache or weakening provider ownership; expose explicit source refresh consistently for source-only and agent init; preserve saved-operation reconciliation.

**Non-Goals:** Change global profile selection, installed-skill routing, provider migration mechanics, hook identity rules, or upgrade removal semantics. Authorize arbitrary hook edits, skill overwrite or shared-manager self-update. Optimize provider tree verification or promise a latency target. Add a configurable TTL, a generic utility, or an upstream provider feature.

## Decisions

### 1. Override retrieval freshness on the existing manager profile

For ordinary missing-selection preparation, supply an application-owned immutable `refresh_policy` definition with `mode=max_age` and `seconds=86400` to `explicit-update`, referencing it through `retrieval_policy_refs`. Use the existing deterministic policy-identity mechanism and consume the manager's returned expansion. Preserve the profile's manual acquisition updates, retention and restrictions.

For explicit refresh, including upgrade and init force, select always-refresh retrieval and always-update acquisition. Never combine the 24-hour override with forced refresh. Persist the exact expanded policies in pending intent as today; retries must reuse that intent rather than recompute it. Existing pending operations retain their original policy even when created by an older release. An attempt to switch a pending ordinary operation to force remains a reconciliation error.

The user selected a 24-hour window over indefinite cache reuse. Switching wholesale to the provider's managed profile would also change acquisition defaults; copying its catalog locally would violate manager expansion. Cache-only with fallback would require extra failure classification and recovery paths that this bounded override avoids.

### 2. Keep consumer retention distinct from shared retrieval freshness

Ordinary ensure retains its current fast path, independent of TTL. Only a missing consumer selection asks the manager to consider cache age. A second consumer obtains its own group, claim and pin from the public API even when using the same shared material. No private Saucepan files are read for cache selection, timestamp decisions, or policy mutation. Cache eligibility is manager-owned and does not guarantee zero local integrity-verification work.

### 3. Add an explicit refresh mode for init

Add the Boolean `--force` flag to init with help text describing source refresh, verified unmanaged-manager migration, and guarded hook receipt repair for an explicitly selected agent. Thread a distinct refresh source mode through `open_workspace` and `install_consumer`, mapping it to `SaucepanSources.acquire`. Both ensure and refresh modes require manager readiness, candidate rejection on failures, and publication only at the existing successful boundary. Source-only init commits after full composition; agent init commits only after provisioning succeeds.

Do not implement force as deleting the consumer receipt, clearing the store, or invoking upgrade with an inferred agent. Thread separate internal migration and hook-repair authorizations from init's explicit flag; refresh mode alone must not grant them, since upgrade already refreshes sources. Do not pass init's flag to skill force. Init with an agent continues guarded provisioning and does not gain upgrade's obsolete-skill removal behavior. Explicit force refresh must also work when the consumer has no prior claim.

### 3a. Delegate authorized migration to the official provider

Extend the existing managed inspection/setup adapter with explicit migration intent, defaulting to false. When init force needs the default manager and identifies a supported unmanaged candidate, hash the observed raw file with Python's existing hashlib facility, report the root/digest/operation, and pass migration consent plus that digest to the verified pinned official installer. Use literal arguments, external staging, and the existing setup result parser/reinspection. Saucepan remains responsible for eligibility, expected-digest recheck under coordination, verified backup, publication, and receipts. Never relocate or replace the file from Powerspec itself.

Force is explicit consent to this bounded migration, not proof that the candidate is eligible. Provider rejections for changed bytes, links, unknown sidecars, binary-only/uninitialized roots, unsupported stores, or busy files remain failures. Existing ready managers are reused without self-update. Explicit standalone overrides and injected clients remain untouched. No source demand means no manager work.

Pending/conflict or uncertain setup outcomes retain their original operation identity and require provider recovery; a repeated forced invocation must not invent a new migration or replay setup blindly. Inspect provider state, including through an external setup-capable manager if the shared launcher is unavailable. Reuse the current pinned installer/protocol and receipt handling rather than creating another installer, rollback engine, or private metadata reader.

### 3b. Reuse ZuAT's guarded hook repair

With an explicit agent, init force passes `repair_hooks=True` to existing hook reconciliation. A complete, uniquely identified, owned receipt conflict with source-matching content uses `update_asset(force=True, receipt_only=True)`. ZuAT rechecks source equality inside the mutation. Report its operation identifier on both success and failure, preserving the native bytes and modification time on repair. Ambiguous identity, invalid receipts, locally edited content and cross-provider targets remain failures; source-only init performs no hook inspection or repair.

This broadens init's explicit option while preserving prior ownership decisions. Upgrade retains its current `--force` skill semantics and separate `--repair-hooks` authorization. Dedicated new recovery flags were considered, but the user's requested init force supplies this bounded consent without additional prompts. Successful manager migration or hook receipt repair can remain completed when a later source/asset operation fails; report those completed effects rather than claiming an all-or-nothing rollback.

### 4. Report observable stages

Use neutral resolving/preparing labels at the workspace boundary. At the source-store decision point, report validated retained-selection reuse, preparation allowing the 24-hour cache, or an explicit refresh request. Retained reuse is reported only after binding validation succeeds. `prepare_group` alone does not establish whether the provider fetched, so do not print a definitive cache hit or download absent returned evidence. Preserve the existing progress observer, heartbeat, stderr routing and silent library behavior; no new portable helper is needed.

### 5. Verify effects, not elapsed-time thresholds

Extend source unit tests for expanded policy overrides, unchanged retained-pin lookup, forced existing/missing selections, and pending-intent reuse. Add actual init-entrypoint tests for force with and without an agent, invalid-agent early failure, candidate publication, and guarded skill/hook behavior. Extend official-installer fixture tests for migration consent/digest arguments, verified backup, rejected candidates, uncertain response handling, and repeat behavior. Reuse real ZuAT tests for stale matching receipts, content races, recovery identifiers and preservation of unrelated hooks; no live user installation is a mutation fixture.

Use the real pinned manager with short isolated Windows paths, local Git origins, separate consumer receipts and one shared store. Count Git clone/fetch operations via trace output and compare revisions/pins. Verify cold retrieval, second-consumer warm reuse, same-consumer reuse, warm offline success, explicit refresh after an upstream commit, and preservation of the other consumer's selection. Use Saucepan's existing hidden `--test-now` argument through a test-only transport to cover 86399/86400-second boundaries, future-dated evidence and expired-offline failure without sleeping or editing private store metadata. Keep that clock control out of production code.

## Risks / Trade-offs

- A new consumer can initially see a revision up to 24 hours old -> document the window and `init --force` / explicit upgrade escape paths.
- Provider verification/materialization may remain costly even without fetches -> assert network/revision behavior, record timings diagnostically, and treat further provider optimization separately.
- Additional refresh source mode can miss failure cleanup -> test rejection and prior-pin preservation for composition and agent-provisioning failures.
- Force can affect a shared manager and user-level hook receipts -> enumerate those effects in CLI help/progress, pass explicit internal authorizations, preserve provider backups, and retain recoverable operation identifiers without automatic mutation retries.
- Saved operations can still use the previous always-refresh policy -> preserve exact retry semantics and explain that the new policy applies to new operations.
- Main CLI synchronization text conflicts with the remote-sources read-only sync contract; current sync uses lookup -> this change preserves lookup behavior and leaves that pre-existing spec discrepancy outside scope.
- Historical memory could not be verified because the installed zmem CLI is the Python/service interface rather than the skill's required engine -> decisions above are grounded in current source, public provider contracts and reproduction evidence.

## Migration Plan

No consumer-state rewrite is needed. Ready managed installations remain unchanged; a supported unmanaged installation can be migrated on demand by explicit init force. New source operations use the new policy definitions; existing retained selections and pending operations remain usable. Publish ordinary package updates only after verification. Rolling back to the current 0.1.6 restores its previous init behavior while preserving provider migration state, backups, pins and saved operation receipts. Do not restore raw files over a managed launcher, roll back to older raw-replacement consumers, or delete old policy records and retained outputs.

The separate machine repair completed on 2026-10-22: the verified official installer migrated the default manager to v0.11.0, retained the raw executable backup, and reported ready; global Powerspec was updated to 0.1.6 before migration. Both initial and repeated plain init succeeded afterward, with no clone/fetch on the repeated run.

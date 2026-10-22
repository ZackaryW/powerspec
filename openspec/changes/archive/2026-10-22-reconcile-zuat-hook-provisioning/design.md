# Design

## Context

See proposal.md for motivation. `provision_hooks` currently falls through from indeterminate inspection to install and rejects all unowned hooks. `upgrade_consumer` reconciles hooks before obsolete-skill removal; its force parameter currently applies only to skills. ZuAT's public example demonstrates the required inspection decision table.

## Goals / Non-Goals

**Goals:** Consume complete ZuAT ownership evidence, make receipt repair explicitly selectable, and verify behavior against the pinned dependency.

**Non-Goals:** Native hook parsing or receipt editing in Powerspec, automatic live installation repair, positional overwrite compatibility, unrelated routing work, and a Powerspec release/version bump.

## Decisions

- Pin ZuAT 0.1.2 at published corrected commit `b2cb2dc72d31a0aed5b55d5597fc2f56e3017941`, preserving the repository's immutable Git dependency convention. Refresh uv.lock and test the installed package rather than a local source override.
- Integration exposed an additional upstream false-success bug when deleted native hooks retain a valid receipt. The user explicitly authorized ZuAT change `restore-missing-owned-hooks`. The corrected package was first verified through a source-matched wheel, then published as commit `b2cb2dc72d31a0aed5b55d5597fc2f56e3017941`. The final immutable pin includes missing-group restoration and the receipt-only guard; the original `170f18b8` revision did not.
- Keep the decision table in feature-owned provisioning code. ZuAT already owns portable group selection, locking, recovery, and receipt mechanics; no new generic helper is needed.
- Check completeness before reuse or mutation. Use `update_asset` for outdated owned groups, unforced `install` for verified absence or exact unowned adoption, and reject all other states unless eligible for explicit receipt repair. Exact adoption reports reused; receipt repair reports updated with an explanatory diagnostic and operation ID.
- Thread a default-false `repair_hooks` option from `upgrade --repair-hooks` through `upgrade_consumer` to provisioning. Use `update_asset(..., force=True, receipt_only=True)` only for complete owned source-matching conflicts. The provider-side guard rechecks ownership and source equality inside the update operation so a concurrent restoration of old hooks cannot turn repair into replacement. The user approved this upstream API extension. Extending skill `--force` would silently broaden existing authorization and is rejected. Init retains normal reconciliation with guidance to run explicit repair through upgrade.
- Preserve failed provider results and operation IDs. CLI output includes hook operation IDs so recovery remains accessible after process exit.

## Risks / Trade-offs

- Ambiguous legacy or duplicate groups now stop instead of appending callbacks → actionable diagnostics and regression tests; users resolve ambiguity explicitly.
- Upgrade refreshes sources before reaching hook repair → document that this option remains part of normal upgrade and does not constitute a standalone repair command.
- Provider behavior can differ from mocked states → exercise Codex and Claude fixtures using real ZuAT, including adoption, stale receipt repair, unrelated settings, no duplication, and repeat reuse.

## Migration Plan

Update dependency and lock together, implement the decision table and CLI option, and run focused then full tests. Existing receipts remain managed by ZuAT. A repair returns a provider recovery operation ID; Powerspec never edits receipt storage itself. Rollback of this code/dependency change is a source revert, not an automatic reversal of already completed provider operations.

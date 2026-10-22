# Proposal

## Why

Initializing a second folder fetches both globally selected Git sources even when another consumer has just populated the shared Saucepan cache. Isolated Powerspec 0.1.6 runs measured 57 seconds for an empty cache, 0.66 seconds for the same consumer, and 69 seconds with two fetches for a new consumer sharing that cache; generic preparation messages also obscure retained-source reuse.

## What Changes

- Use Saucepan's public refresh-policy override to reuse valid shared retrieval material younger than 24 hours when ordinary init creates a missing consumer selection; refresh expired or missing material.
- Preserve exact existing consumer selections regardless of shared-cache age unless explicitly refreshed.
- Add `pspec init --force` to refresh selected sources immediately, with or without `--agent`, bypassing both retained-selection reuse and the shared-cache age window.
- Distinguish retained selection reuse, cache-eligible preparation, and explicit refresh in stderr progress without claiming unobserved downloads or cache hits.
- Let `init --force` explicitly authorize provider-verified migration of a supported unmanaged Saucepan installation when source preparation needs it, with a verified backup and retained recovery receipts.
- Let `init --agent <agent> --force` authorize ZuAT's guarded receipt-only repair of source-matching owned hooks. Preserve consumer ownership, retained pins, uncertain-operation recovery, and explicit upgrade behavior; force still does not authorize arbitrary skill/hook replacement or manager self-update.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `remote-sources`: Specify bounded shared retrieval freshness, explicit init refresh, and manager-expanded policy overrides.
- `cli-product-surface`: Add init's source-refresh and guarded-recovery option and evidence-based progress states.
- `managed-saucepan-binary`: Treat init force as explicit verified-migration authorization while preserving provider preflight, backup, receipt and recovery contracts.

## Impact

Application-owned source policy and selection in `src/powerspec/sources.py`, workspace resolution in `workspace.py`, init argument handling, managed installer invocation, agent-install integration, related CLI/provider tests, and usage documentation. Reuse existing Saucepan 0.11 / SDK 0.3 migration and ZuAT guarded-repair APIs without a new dependency or upstream change. The already-completed machine migration supplies environment evidence; implementation and tests must exercise disposable installations instead of migrating that ready installation again.

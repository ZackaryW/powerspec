# Proposal

## Why

OpenSpec 1.15 reports requirement text longer than 500 characters as a warning, so `openspec validate --specs --strict` now fails for 13 of the 17 main specs (90 requirements). Long requirement paragraphs bundle several behaviors and edge cases that are easier to verify as scenarios. Strict validation should pass again so it can keep acting as a gate.

## What Changes

- Shorten each of the 90 flagged requirements to 500 characters or fewer without changing its normative meaning.
- Keep the core SHALL statements in the requirement text, and move examples, edge cases and conditional details into scenarios.
- Split a requirement into separately named requirements only where it states clearly separate behaviors. The original keeps its name and its primary behavior.
- Existing scenarios are preserved; new scenarios restate behavior that the original paragraph already required.
- No behavior, code or documentation changes, with two deliberate wording corrections:
  - `cli-product-surface` "Upgrade refreshes before committing removals" said init --force grants hook repair "without granting skill replacement". That sentence was stale after init --force gained skill replacement authority, which the same spec's "Forced initialization authorizes bounded recovery" requirement already states. The restructured text no longer contradicts it.
  - Two historical notes in `profile-skill-bundles` that described an earlier change's scope ("does not require implementing general synchronization in this change", "publication remains future sync work") are dropped; they stated no behavior.
- Out of scope, recorded for follow-up: `context-sync` and `cli-product-surface` say sync acquires missing sources, while `remote-sources` says sync never fetches; `remote-sources` describes `@gitsource` references as supported in one requirement and rejected in another. Meanings are preserved unchanged here.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `cli-product-surface`: restructure 12 long requirements.
- `consumer-configuration`: restructure 3 long requirements.
- `context-sync`: restructure 6 long requirements.
- `managed-saucepan-binary`: restructure 4 long requirements.
- `package-distribution`: restructure 2 long requirements.
- `profile-skill-bundles`: restructure 16 long requirements.
- `remote-sources`: restructure 8 long requirements.
- `repository-investigation`: restructure 2 long requirements.
- `skill-bootstrap`: restructure 5 long requirements.
- `skill-content-resolution`: restructure 6 long requirements.
- `trait-hook-delivery`: restructure 7 long requirements.
- `user-skill-installation`: restructure 4 long requirements.
- `workset-launch`: restructure 15 long requirements.

## Impact

- Specs only: 13 files under `openspec/specs/`.
- Requirement names stay stable except where a split adds a new requirement; `/opsx:verify` and history references to existing names keep working.
- Success: `openspec validate --specs --strict` passes for all 17 main specs.

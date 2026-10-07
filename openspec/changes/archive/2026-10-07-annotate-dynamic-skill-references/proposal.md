# Proposal

## Why

The universal bootstrap currently sends ordinary skill invocations through Powerspec's installed-copy discovery, duplicating the agent's native skill integration and producing avoidable ambiguity when user and project copies coexist. Dynamic-resolution instructions should instead accompany the specific generated guidance that mentions a manifest-backed skill, so the agent retains discovery and selection ownership.

## What Changes

- Automatically classify explicit `<skill:name>` references from their selected catalog resources using `pspec.toml`, including manifests that only declare inputs. Classification does not evaluate runtime inputs or assemble skill procedures.
- Add a section heading and concise handoff instructions to each emitted configuration guidance block or runtime trait message that mentions dynamic skills. Deduplicate names within the block, preserve ordinary mentions, and reconcile generated headings with their owning contributions.
- Replace the universal pre-skill bootstrap reminder with targeted guidance. Bundled dynamic skill entrypoints also describe the handoff for direct native invocation; ordinary skills require no Powerspec lookup.
- **BREAKING:** Make runtime skill content resolution consume an explicitly supplied skill location rather than discover installed copies by name or validate native precedence through ZuAT. Preserve the existing assembly, pending-input, project-context, and read-only contracts.
- Reject the former name-based command with actionable migration instructions. For eligible runtime messages, inspect available source metadata without acquisition; explicitly identify unknown classification when operational availability prevents inspection, preserving independent guidance.
- Update resource delivery, specifications, CLI guidance, examples, and regression coverage together so installation reconciliation does not reintroduce the universal reminder.

## Capabilities

### New Capabilities

None. Extend the existing guidance and content-resolution capabilities.

### Modified Capabilities

- `context-sync`: Classify explicit skill references and publish dynamic-resolution headings inside their owning managed guidance blocks.
- `trait-hook-delivery`: Apply the same targeted annotation to eligible runtime trait messages and replace universal bootstrap delivery while preserving lifecycle and no-input/no-mutation boundaries.
- `skill-bootstrap`: Replace mandatory lookup of every skill with native selection followed by an explicit, conditional dynamic-content handoff.
- `skill-content-resolution`: Consume the caller's selected skill location directly and preserve manifest assembly and invocation-local configuration behavior.
- `cli-product-surface`: Define the explicit-location skill command and migration behavior for the existing name-based invocation.

## Impact

- Reference compilation and delivery: `src/powerspec/conditions.py`, catalog resource metadata, `hooks.py`, and managed YAML reconciliation in `syncing.py`.
- Runtime command boundary: `src/powerspec/cli/skill.py` and the installed-discovery bridge in `installed.py`; the manifest and assembly functions in `skills.py` remain the foundation.
- Bundled profile, trait, and skill guidance under `.pspec/`, plus README, skill-resolution/context-sync/hook documentation, and packaged-resource assertions.
- Focused tests for reference classification, generated headings, YAML preservation and idempotence, hook output and unavailable remote metadata, explicit-path CLI behavior, pending reruns, and packaged guidance.
- ZuAT remains responsible for provisioning and its ownership checks. This change does not redesign installation scopes, profile composition, source acquisition, dynamic manifest version 2, or OpenSpec's YAML schema.

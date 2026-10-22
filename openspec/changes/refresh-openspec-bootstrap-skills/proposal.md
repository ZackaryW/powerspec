# Proposal

## Why

The installed OpenSpec CLI is 1.14.3, but Powerspec bundles an older upstream skill revision and its repo-local generated skills still identify 1.12.0. Refreshing both sources makes bootstrap deliver the current artifact-containment and precise task-tracking instructions.

## What Changes

- Pin all twelve existing bundled OpenSpec skill roots to the immutable v1.14.3 commit, preserving build-time acquisition and offline runtime behavior.
- Refresh this repository's generated agent skills through the installed OpenSpec update command.
- **BREAKING**: Require OpenSpec 1.14.3 or later for fresh bootstrap and report older versions as incompatible in doctor, matching the bundled skill contract.
- Update compatibility documentation and verify direct-wheel/source-distribution parity, isolated installation, and bootstrap behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `package-distribution`: Keep the packaged workflow snapshot and documented/enforced CLI compatibility floor aligned.

## Impact

Changes affect pyproject.toml's build-source revision, generated .agents/skills files, initialization and doctor version checks, focused tests, and packaging/initialization documentation. The existing Hatch snapshot mechanism and pspec-skill-bootstrap handoff remain in place. Global installed skills and the separate add-pspec-skill-routing change are outside scope. Commits remain local; no push or release is authorized.

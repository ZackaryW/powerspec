# Proposal

## Why

Hook resolution currently waits for a native JSON document on stdin before discovering its consumer. This unrequested transport dependency can block a direct invocation while stdin remains open; the intended command already has its event and agent arguments and can discover configuration from its process working directory.

## What Changes

- **BREAKING**: Stop reading or requiring native hook payloads on stdin. Resolve the consumer from the command's process working directory; piped payloads no longer select a different repository.
- Pass explicit invocation cwd into hook dispatch and condition evaluation, retaining Git/worktree boundaries and explicit `--change` selection.
- Keep native event/source filtering in installed callback matchers, with event and agent arguments selecting the supported dispatcher mapping.
- Return guidance and any request for the agent to obtain user input through stdout context; never conduct an interactive stdin exchange.
- Preserve native response serialization, silent no-guidance results, stderr diagnostics, bounded probes, and existing lifecycle-only registrations.
- Replace payload-dependent tests and documentation with no-input and open-stdin regressions.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli-product-surface`: Define hook resolution as an argument-and-working-directory command that never consumes stdin.
- `trait-hook-delivery`: Make process cwd authoritative, assign native source filtering to registration matchers, and specify noninteractive context delivery.

## Impact

Affected implementation: `src/powerspec/cli/hook.py`, `src/powerspec/hooks.py`, hook dispatch callers/tests, and `docs/hook-delivery.md`. No new library, generic utility, source acquisition, or installation surface is needed. Existing generated command strings and native output envelopes remain compatible. Callers previously selecting a repository through payload `cwd` must instead set the process cwd. Archived changes remain historical records; this change supersedes their stdin assumption through current-spec deltas.

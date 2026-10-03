# Proposal

## Why

Installing bootstrap makes it available but does not deliver its reminder to a session. Add trait-owned hook guidance so the same user-level dispatcher can introduce bootstrap at session start and restore it after compaction using each repository's current configuration.

## What Changes

- Add the bootstrap runtime trait and reference it from the global builtin profile.
- Map logical/native selectors and per-trait native exclusions without removing shared registrations.
- Implement pspec hook using event context and the shared Git-bounded consumer resolver.
- Evaluate matching traits' Python when expressions afresh with the foundation's invocation/variable bindings and command-JSON helper, without persisting results.
- Provision generic user-level hook callbacks through ZuAT during initialization for the explicit agent.
- Verify actual native context delivery separately from command invocation and agent adherence.

## Capabilities

### New Capabilities

- `trait-hook-delivery`: Trait event selection, consumer-specific dispatch, native context delivery, and generic callback provisioning.

### Modified Capabilities

None. Context/trait ownership and profile composition are owned by profile-skill-bundles; this change consumes them.

## Impact

Depends on establish-profile-consumer-resolution, implement-skill-content-resolution, and bundle-resources-and-initialize. Extends src/powerspec/cli/hook.py and initialization's ZuAT adapter, plus builtin resources. Does not put hook bodies into config.yaml or move selectors into profiles.

Completion means supported sessionStart and afterCompaction surfaces deliver selected bootstrap guidance in isolated native integrations, with preserved unrelated settings and honest unsupported reports. No testing workflow starts from a hook. Broader hook vocabulary, full sync, and flush are excluded.

Dispatch consumes the shared trusted Python-condition contract, including authored run_json probes. It does not evaluate skill hints or automatically migrate CodeGraph/zmem bundles. Errors are diagnostics; false omits only its trait and preserves generic registrations.

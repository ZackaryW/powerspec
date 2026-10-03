# Design

## Context

The Saucepan Python SDK defaults to the shared executable under `~/.saucepan/bin`, but it does not install that executable. Zuu case17 composes GitHub release resolution, platform asset selection, staged probing and validation, atomic publication, cached update checks, and fallback to a compatible installed binary.

## Decisions

### Declare the verified CLI protocol range

Accept Saucepan CLI 0.5 and 0.6 releases, the two protocol lines verified with the installed Python SDK boundary. CLI and SDK release numbers are independent, so matching the SDK major/minor would reject a supported 0.6 executable. Reject other CLI lines during candidate selection and installed-baseline validation.

### Manage only the SDK's shared executable

Create the shared executable's parent directory, then configure Zuu `ManagedReleaseBinary` for `ZackaryW/saucepan`. Probe candidates with `--version`, validate staged candidates with `--help`, and cache successful checks beside the shared binary for 24 hours. Use a policy identifier containing the supported CLI lines so a compatibility-policy change invalidates freshness.

### Provision only default clients

`SaucepanSources()` waits until its first actual source operation, then ensures the binary before it constructs and retains its default SDK client. `SaucepanSources(client)` uses the supplied client directly. This preserves isolated tests and explicit alternative clients, keeps bundled-only catalog construction offline, and makes selected remote operations self-bootstrapping.

### Preserve Zuu fallback semantics

If discovery or upgrade fails while a compatible executable is present, retain it as Zuu specifies. If no compatible executable can be produced, convert the managed-tool failure into a Powerspec configuration diagnostic. Source operations remain responsible for their existing Saucepan-level diagnostics after client construction succeeds.

## Risks / Trade-offs

- A first remote-source operation now needs network access when Saucepan is absent; failure is explicit and leaves no partial executable.
- Freshness caching can defer a newly published compatible release for up to 24 hours; this avoids release discovery on every hook or sync invocation.
- GitHub release validation proves executable identity and behavior but does not add a separate signature system beyond the release transport and Zuu lifecycle.

## Verification

Exercise manager configuration and default-client construction with isolated paths and fakes, prove injected clients bypass provisioning, retain the existing opt-in real Saucepan acceptance, run focused source tests, then run the full suite and strict OpenSpec validation.

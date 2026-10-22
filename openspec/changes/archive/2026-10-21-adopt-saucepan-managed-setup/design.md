# Design

## Context

See `proposal.md`. At `f97b955`, `saucepan_tool.py` uses Zuu `ManagedReleaseBinary` to extract only the manager and replace `~/.saucepan/bin/saucepan`; `saucepan_bootstrap.py` initializes externally before publishing into that slot. `sources.py` lazily creates the SDK client, while doctor probes version only. The SDK pin already corresponds to Saucepan v0.10.0, whose command surface lacks the proposed setup/status contract.

The linked provider design is `../../../../../saucepan/openspec/changes/archive/2026-10-21-add-managed-setup/design.md`. Its public result schemas, script inputs and explicit migration behavior are the prerequisite. Existing `add-pspec-skill-routing` touches some of the same source/lifecycle code but remains a separate change.

## Goals / Non-Goals

**Goals:** preserve authorized first-use convenience, use Saucepan-owned managed installation, distinguish installation from source readiness, and keep read-only calls bounded.

**Non-Goals:** shared auto-update, user-store migration during development, SDK installation hooks, rewriting Saucepan's metadata, replacing explicit user-managed binaries, or changing skill routing and source retention.

## Decisions

### 1. Use the provider's installation result and inspection contract

Keep a feature-owned adapter in `saucepan_tool.py`/`saucepan_bootstrap.py`. The default path remains the shared launcher location, but filename existence and the old `saucepan-check.json` no longer establish ownership. Probe an existing executable within existing deadlines; when it supports setup, inspect through `setup-status` and accept only a ready managed installation with a compatible protocol. Cross-check the returned root/launcher and observed version. Propagate pending/corrupt/unmanaged states as distinct diagnostics.

An old default raw manager cannot report setup status; classify it as requiring migration, not missing and replaceable. Show official migration instructions with an observed expected digest, but do not execute migration or backup based on init/upgrade alone. A user-selected `POWERSPEC_SAUCEPAN` remains an explicit standalone mode: inspect compatibility, never install/update/adopt that file. An injected SDK client still bypasses manager provisioning entirely.

Alternative: retain Zuu's fallback replacement for old clients. Rejected because it can overwrite a real shim and restore competing update ownership.

### 2. First setup stages a verified official installer; no store mutation in the adapter

Only an already-authorized source-materializing operation can initiate first setup. Use an immutable provider release descriptor containing tag, SDK revision, platform support, installer identity and checksum. Download/verify the official script in a temporary directory outside the store, invoke with literal arguments through existing process utilities, and pass an explicit operation UUID. The script verifies/stages the release manager/shim and Rust performs setup. Do not hand-build policies, call init separately, copy raw binaries into the store, or edit receipts.

Propagate setup stdout/status, backup/retry identities and incomplete outcomes without automatic mutation retries. Keep lifecycle progress on stderr. Reinspect the returned managed launcher before creating the source client. Follow the provider's root selection; do not infer a store from cwd. Missing shell prerequisites produce actionable setup instructions rather than an alternate raw installer.

The exact new release tag and immutable SDK commit must be selected from actual provider implementation/release evidence, not invented during planning. The release descriptor is a deployment prerequisite. Local tests use an explicit build/fixture descriptor. Production acceptance cannot be marked complete while only an unpublished placeholder is available.

### 3. Reuse and update ownership

Normal init, sync, lookup and upgrade reuse a compatible managed launcher without manager release discovery. `pspec upgrade` refreshes selected resource sources and agent assets only; it does not invoke self-update. Incompatibility reports installed/supported versions and explicit provider update guidance. Saucepan's `self-update APP CLAIM --tag TAG` is the authorized shared version change; Powerspec does not reimplement tag selection or activation.

Remove the app-owned 24-hour manager refresh cache from decision-making. Leave old cache files untouched rather than treating cleanup as ownership proof. Keep existing selected-source refresh/recovery/pinning behavior unchanged.

### 4. Doctor distinguishes evidence

Retain the compatible executable observation, add managed installation state when the provider supports inspection, and explicitly label standalone overrides. Neither managed readiness nor a compatible version proves selected sources are prepared or host hooks received guidance. Do not repair during doctor, status, hook or skill protocols. Use one shared deadline across executable and setup inspection where a hook budget applies; no network discovery on this path.

### 5. Utility reuse and verification

Reuse `inspect_executable(argv, *, cwd, timeout, parse_version=None, creationflags=0)` for bounded version inspection. `run_json_object(argv, *, cwd, env, timeout)` is suitable for successful read-only object responses, but discards stdout on nonzero exit and therefore cannot preserve setup's exit-2 receipt. Use standard `subprocess.run` with literal argv, `shell=False`, captured stdout/stderr and an explicit timeout in the feature-owned installer adapter; interpret exit 0/2 and uncertainty there. Reuse `tempfile`, `pathlib`, `hashlib` and standard HTTP/file APIs for staging and checksum mechanics. Lifecycle policy, exact release descriptor parsing and setup result validation remain feature-owned; no generic utility or new dependency is planned. Existing utility contract tests remain applicable without changing those APIs.

Use TDD for the behavioral adapter and CLI diagnostics under the repository's apply guidance. Focused tests must cover unmanaged old managers, ready/pending/conflict provider output, malformed responses, setup response loss, no-network reuse, explicit overrides, injected clients, and deadlines. Real provider acceptance uses its built manager/shim and loopback release fixture through the actual Powerspec entrypoint in isolated homes. Verify user-home and existing consumer state are untouched, source receipts still retain exact generations, and no direct write reaches Saucepan's launcher or metadata.

## Risks / Trade-offs

- Older Powerspec releases can still replace the shared path -> document the minimum safe consumer version and disable their use of that default location before actual migration; no claim that the new adapter controls old executables.
- Provider release gate was resolved by published v0.11.0 and SDK 0.3.0 at commit `324282bac14fd0e0032a07e0fbed85ee95447dbb`; see `verification.md` and `release-acceptance.json`.
- Shell installers add a prerequisite at first use -> fail before store effects with manual official setup guidance; normal runtime needs only the installed manager.
- Skill-routing implementation can overlap this work -> preserve its selection semantics and rerun relevant source/protocol tests after merging; do not count either change's tests as proof of the other.

## Migration Plan

1. Implement and validate Saucepan `add-managed-setup` first; record its public contract and immutable SDK/build evidence.
2. Replace the adapter and verify it against local provider fixtures, preserving standalone override support.
3. Select actual published installer/SDK artifacts for the production descriptor and run isolated installed-package acceptance.
4. Document the explicit user-run raw-manager migration. Do not perform that host action as part of tests or apply.
5. On rollback, retain the managed installation and use a compatible explicit executable path with older Powerspec where necessary; never allow its legacy default updater to replace the shim.

## Implementation evidence

The provider contract was archived on 2026-10-21 and released as v0.11.0. The consumer now pins its exact installer checksums and SDK commit. Windows provider canonical paths use an extended prefix, which the adapter normalizes for root/launcher comparisons. Default SDK clients explicitly retain the inspected root, so ambient `SAUCEPAN_ROOT` cannot redirect subsequent source operations. See `verification.md` for acceptance, the unrelated baseline workset failure, and the corrected test-isolation incident.

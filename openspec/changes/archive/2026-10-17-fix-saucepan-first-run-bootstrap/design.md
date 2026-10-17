# Design

## Context

See proposal.md for the failure chain. `ensure_saucepan_binary` currently creates the final parent before Zuu's managed-release staging. `SaucepanSources._application` only initializes after registration reports unsupported_store. Saucepan 0.10 intentionally requires an empty root or its own interrupted-initialization marker. Doctor checks versions, not materializations. Existing source acceptance tests inject a manager and therefore bypass the failed ordering.

## Goals / Non-Goals

**Goals:** Correct default first use, bounded preservation of failed installer leftovers, retryable errors, and realistic isolated acceptance evidence.

**Non-Goals:** Rust changes, store migration, weakened authentication, making upgrade silently perform init, or full transactional rollback of source provisioning.

## Decisions

1. Keep orchestration in a feature-owned `saucepan_bootstrap.py`, called by `saucepan_tool.ensure_saucepan_binary` for the canonical default location. The binary updater remains Zuu case17. Pass the existing manager factory and validator into bootstrap to avoid circular imports and retain the supported binary contract. Explicit destinations outside the default path retain today's managed binary behavior. Injected SDK clients continue bypassing provisioning.
2. Serialize default ensure/bootstrap with an exclusive sibling lock outside the store. Follow the existing consumer-operation lock convention: fail clearly on an occupied lock; never automatically remove another process's lock. An abruptly killed process requires confirming it stopped before removing that named lock.
3. Use root layout only to select safe bootstrap eligibility, not to interpret or trust metadata. A root with root.json delegates all validation to Saucepan's normal operations and skips init. A missing/empty root bootstraps. Saucepan's `.staging/initializing.json` allows retry through its own init guards. Unknown uninitialized roots fail before binary publication. Reject linked root/bin/recovery files.
4. Stage and validate in a temporary sibling directory on the same filesystem. For eligible binary-only leftovers, first validate and copy the existing manager and reuse its check record when applicable. Revalidate the recognized layout after staging. Rename only the recognized bin directory into a unique, persistent sibling backup (`.powerspec-saucepan-backup-*`). Never remove backups automatically. Then call `Client(executable=external, root=shared).init()` and atomically rename the staged executable to the final destination. If init or publication fails, report the backup location and preserve Saucepan's partial initialization for guarded retry.
5. Reuse Zuu's public `CheckState`/`FileCheckStateStore` and dataclass replacement to transfer the successful check between the staging and final destination identities. Only change destination identity; keep source, policy, version, and check time. Match Zuu's normalized absolute-path identity and verify immediate reuse without discovery. A malformed/missing/unwritable check record never destroys a usable binary; it causes the next check to run normally.
6. Keep doctor read-only and its `saucepan` check name stable, but label a successful result as executable compatibility with store/source readiness unchecked. Document init retry before upgrade.

### Utility and dependency assessment

No new portable utility contract is needed. Zuu already supplies downloading/staging/probing and successful-check persistence; the SDK supplies initialization; pathlib/tempfile/shutil/os and dataclasses supply preservation and same-filesystem publication. Eligibility, backup naming, lock diagnostics, and initialization ordering are PowerSpec's Saucepan integration policy and belong in the feature module. Do not invent generic recovery abstractions or add a locking dependency for this bounded protocol. Existing executable inspection remains unchanged.

## Risks / Trade-offs

- Process termination leaves a lock or backup → retain data, document lock recovery and permanent backup path; never silently reset a store.
- Another tool can mutate the root outside PowerSpec's lock → recheck eligibility before relocation and let Saucepan's initialization guards reject incompatible state. This lock coordinates PowerSpec, not arbitrary external writers.
- Disk errors after init → preserve the initialized root; rerunning provisioning can publish the executable without reinitializing it.
- Backup retains an executable copy → intentional conservative recovery; user can remove it after confirming successful setup.
- Native basic init remains authoritative → no mandatory keyring and no Python emulation of Saucepan metadata.

## Migration Plan

Install the updated PowerSpec package and rerun the original init command. Existing valid stores and selections are reused. Verify fresh/recovery homes and real Git acquisition before retrying the user's interrupted setup. Rollback leaves valid store metadata and backups intact; older PowerSpec can consume the initialized store. No schema migration or compatibility fallback is introduced.

## Live integration finding

The installed retry exposed a source-identity comparison defect after store initialization: Saucepan canonicalizes HTTPS GitHub owner/repository paths to lowercase. Accept that canonical spelling while preserving host, transport, query, and reference distinctions; retain case sensitivity for other remote hosts. A focused failing regression was observed before the narrow comparison fix, followed by 28 passing source tests.

# Proposal

## Why

Powerspec acquires remote skill sources through the old Saucepan. The integration spans a Python SDK pinned to a Saucepan commit, signed installer scripts with setup receipts and migration records, and a store model of applications, groups, claims, policies and pins. That Saucepan is being replaced by a three-project stack:
- **panned:** policy decisions plus a shared CLI protocol.
- **milkpan:** a small GitHub and local-git resource bucket on panned, released with per-platform binaries.
- **the new Saucepan:** extends milkpan.

Milkpan v0.2.0 covers what Powerspec needs: exact-commit snapshots of GitHub and local repositories, per-scope leases, content shared across scopes, stable links, and self-update on the next run. It does this through one JSON protocol instead of an SDK and a store model.

## What Changes

- **BREAKING:** Powerspec's source store uses milkpan instead of Saucepan. The `saucepan-sdk` dependency, the managed Saucepan installer flow (scripts, receipts, migration records), applications, groups, claims, policy expansion and pins are removed. The old Saucepan store and its `saucepan-state.json` are left untouched and ignored. Consumers re-run `pspec init` once to select sources through milkpan.
- **Managed milkpan:**
  - **Bootstrap:** Powerspec pins a milkpan release with a SHA-256 for each platform asset. It downloads and verifies the asset into its own milkpan home (`~/.powerspec/milkpan`).
  - **Self-management:** milkpan then manages itself there, through a lease on its own release and a stable link that Powerspec invokes. A Powerspec release pinning a newer milkpan switches the link, effective on the next run.
  - **Override:** `POWERSPEC_MILKPAN` selects a standalone executable instead.
- **Thin protocol client:** a small Python module runs `milkpan --home <home> --format json --protocol 1 …` and maps the shared envelope and error codes to Powerspec errors. There is no external SDK.
- **Origins:** recipes map to `github:<owner>/<repo>` for `https://github.com/<owner>/<repo>` origins and to `local:<absolute path>` for local or `file://` repositories. Other origins are rejected with a clear error.
- **Selection by exact commit:**
  - **Resolution:** a recipe's reference is resolved in a per-consumer candidate scope, which also caches resolution for a day.
  - **Selection lease:** the consumer's selection is a lease on `@<commit>` in the consumer's scope. It has a stable content path and is the same blob, with no second download.
  - **Commit and reject:** commit publishes the new lease and releases the replaced one; reject releases the candidate.
- **Policy file:** Powerspec owns `milkpan.toml` in its home. A rule per consumer scope and the manager scope keeps selected leases from expiring and sets the one-day refresh.

## Capabilities

### New Capabilities
- `managed-milkpan-binary`: pinned, verified, self-managed milkpan for Powerspec's source store.

### Modified Capabilities
- `remote-sources`: acquisition, sync and upgrade through milkpan leases instead of a Saucepan application; GitHub and local origins only.
- `cli-product-surface`: first-use preparation, sync, upgrade, doctor and progress describe milkpan.
- `user-skill-installation`: bundled skills never need milkpan; milkpan is the acquisition mechanism for user-added remote sources.
- `managed-saucepan-binary`: removed, replaced by `managed-milkpan-binary`.

## Impact

- **Removed:** `saucepan_bootstrap.py`, `saucepan_provider.py`, `saucepan_tool.py`, the `saucepan-sdk` dependency, `tests/saucepan_release_fixture.py` and Saucepan-specific tests.
- **Added:** `milkpan_client.py` (protocol client), `milkpan_binary.py` (pinned release, verify, bootstrap, self-link) and a rewritten `sources.py` (`MilkpanSources` with the same public surface).
- **Callers updated:** `cli/hook.py`, `cli/sync.py`, `cli/upgrade.py`, `installation.py`, `upgrading.py`, `workspace.py`, `doctoring.py` and `statusing.py`.
- **Integration tests:** use local git repositories through milkpan's `local:` provider, and a mock GitHub API (`MILKPAN_GITHUB_API`) for GitHub recipes.
- **Docs:** `docs/remote-sources.md`, `docs/initialization.md`, `docs/foundation.md`, `docs/context-sync.md` and the README.
- **Depends on:** milkpan v0.2.0, which must be released before Powerspec pins its asset digests.

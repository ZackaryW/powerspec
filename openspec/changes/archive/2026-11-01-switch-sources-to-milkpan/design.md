# Design

## Context

See proposal.md. Today `SaucepanSources` (`src/powerspec/sources.py`) is the source store. Its public surface, used by `workspace.py`, `upgrading.py`, `installation.py` and `cli/{hook,sync,upgrade}.py`, is:

| Member | Role |
| --- | --- |
| `consumer_path`, `scope` | Identify the owning consumer config and its scope |
| `for_consumer(path)` | The store for another consumer config |
| `lookup(identity, recipe, *, deadline=None) -> SourceBinding` | Read only; `MetadataUnavailable` when not selected |
| `ensure(identity, recipe)` | Reuse a selection, or prepare with one-day caching |
| `acquire(identity, recipe)` | Explicit refresh |
| `commit()`, `commit_new()`, `reject()` | Two-phase publication of candidates |
| `SourceBinding` | `identity, repository, requested_revision, resolved_revision, source_id, artifact_id, root` |

The surrounding modules handle the Saucepan executable:
- `saucepan_tool.py`: discovery and compatibility;
- `saucepan_bootstrap.py`: the signed installer flow;
- `saucepan_provider.py`: the pinned provider and setup receipts.

`doctoring.py` and `statusing.py` report Saucepan setup state.

Milkpan v0.2.0 provides:
- **`acquire <spec> --scope S`:** returns the lease (id, version, digest), the content path and a `fetched` flag.
- **`reacquire <lease>`:** forced re-resolution.
- **`release`, `lease show`, `path <lease>`, `link`:** per-lease operations and stable links.
- **The `github:` and `local:` providers.**
- **Selector-independent reuse:** the same commit under `@ref` and `@<sha>` is stored once.
- **A `milkpan.toml` of panned `[[rule]]` tables,** with `lease(ttl, refresh, retain)` obligations.
- **Releases:** per-platform `milkpan-v<version>-<target>.(zip|tar.gz)` assets plus `SHA256SUMS`.

## Goals / Non-Goals

**Goals:**
- Keep the source store's public surface, so callers change only the class name.
- Remove the Saucepan SDK, installer, receipts and store model entirely.
- Integration tests run through milkpan alone: `local:` for local repositories, and a mock GitHub API for GitHub recipes.

**Non-Goals:**
- Migrating old Saucepan selections. Consumers re-run `pspec init`; the old store is left alone.
- Origins other than GitHub and local repositories; those wait for Saucepan providers.
- Sharing a user's own milkpan bucket. Powerspec uses its own home, so its policy never conflicts with the user's.

## Decisions

### Protocol client, not an SDK
`milkpan_client.py` exposes `Milkpan(executable, home, timeout)` with methods `acquire`, `reacquire`, `release`, `lease`, `path`, `link`, `protocol` and `version`. Each runs one subprocess, `[exe, "--home", home, "--format", "json", "--protocol", "1", ...]`, with no shell and a deadline-aware timeout. It parses the single envelope from stdout or stderr and raises `MilkpanError(code, message, details)` for `ok: false`. Transport failures (timeout, unparsable output, launch errors) raise `MilkpanUnavailable`.

The sources module maps errors to Powerspec's types:
- `denied`, `invalid_request` and `conflict` become `ConfigurationError`;
- `not_found` and `unavailable` become `MetadataUnavailable` during lookup and `ConfigurationError` during preparation.

Alternative: a published Python SDK for panned tools. Rejected for now; the protocol is small and stable, and Powerspec needs eight calls.

### Managed binary
`milkpan_binary.py` holds the pin:

```python
MILKPAN = Release(tag="v0.2.0", assets={
    ("Windows", "x86_64"): ("milkpan-v0.2.0-x86_64-pc-windows-msvc.zip", "<sha256>"),
    ("Darwin", "arm64"):   ("milkpan-v0.2.0-aarch64-apple-darwin.tar.gz", "<sha256>"),
    ("Darwin", "x86_64"):  ("milkpan-v0.2.0-x86_64-apple-darwin.tar.gz", "<sha256>"),
    ("Linux", "x86_64"):   ("milkpan-v0.2.0-x86_64-unknown-linux-gnu.tar.gz", "<sha256>"),
})
```

The digests are copied from the release's `SHA256SUMS` when the pin is set, and machine aliases (`amd64`, `aarch64`) are normalized. `ensure_milkpan(home)` runs these steps:
1. **Override:** if `POWERSPEC_MILKPAN` is set, check compatibility and return it.
2. **Existing link:** if `<home>/links/milkpan/<exe>` exists and is compatible, and the `powerspec-manager` lease on the pinned spec has the pinned digest, return it.
3. **Bootstrap:** otherwise, if no usable link exists:
   1. download the pinned asset into a temporary directory outside the home (1 MiB chunks, 64 MiB limit) and compare its SHA-256 with the pin;
   2. extract it with `zipfile` or `tarfile`, rejecting absolute and `..` members;
   3. use the extracted executable as a bootstrap.
4. **Self-link:** with the bootstrap, or with the existing link when only the pin changed, run `acquire github-release:zackaryw/milkpan@<tag>#<asset> --scope powerspec-manager`. Then require `lease.digest == pinned digest` and run `link <lease> --name milkpan --file <exe>`.
5. **Return** `<home>/links/milkpan/<exe>`. When the link was just repointed, the current process may keep using the bootstrap or the old link for this run, so the switch takes effect on the next run.

The release asset digest equals milkpan's blob digest (SHA-256 of the asset bytes), so the pin also verifies the managed lease.

Compatibility requires `protocol` to support 1 and `--version` to be in `SUPPORTED_LINES = {(0, 2)}`. Read-only paths call `inspect_milkpan(home)`, which performs only steps 1–2 and raises `MetadataUnavailable` instead of bootstrapping.

### Powerspec's policy file
`<home>/milkpan.toml` is generated and owned by Powerspec. It is rewritten under `<home>/powerspec.lock`, an exclusive create like today's consumer lock. It contains:
- a rule for scope `powerspec-manager`: actions `acquire, reacquire, read, release, link` on `github-release:zackaryw/milkpan*`;
- for each consumer scope `consumer-<sha256>` and its candidate scope `consumer-<sha256>-candidates`, the actions `acquire, reacquire, read, release` on `github:*` and `local:*`:
  - the consumer scope carries `lease(ttl = "36500d")`, so selected leases effectively never expire;
  - the candidate scope carries `lease(refresh = "1d", ttl = "7d")`.

The consumer list is read back from the file, so adding a consumer is append-only. Users are told in docs not to edit it.

### Selection by exact commit
`MilkpanSources` keeps the public surface above. Its state file `milkpan-state.json`, next to the consumer config and git-ignored like today, stores `{consumer, scope, selected: {key: {recipe, spec, commit, lease, digest}}}`. The key is still the SHA-256 of the canonical recipe.

- **`_spec(recipe)`:** `https://github.com/<o>/<r>(.git)` becomes `github:<o>/<r>`; an absolute path, `C:\…` or `file://` becomes `local:<absolute path>`; anything else raises a `ConfigurationError` naming the supported forms.
- **`_prepare(identity, recipe, refresh)`:**
  1. **Resolve:** `acquire <spec>@<reference>` in the candidate scope. This returns the commit and reuses a resolution under a day old, offline. With `refresh`, it is followed by `reacquire <candidate lease>` when the candidate lease already existed.
  2. **Select:** `acquire <spec>@<commit>` in the consumer scope. The same blob is reused through selector-independent storage, giving a lease whose content path never changes.
  3. **Validate:** the path must be a directory and the lease version must equal the commit (and, for a commit reference, the requested commit).
  4. **Record:** keep the candidate `{lease, commit, digest}` in memory and return the `SourceBinding`. Its `source_id` is the spec, `artifact_id` is the lease id and `root` is the path.
- **`commit()` / `commit_new()`:** under the consumer lock, write the candidates into `selected`, then release each replaced commit lease unless another selected recipe still uses it.
- **`reject()`:** release candidate commit leases that are not selected.
- **`lookup()`:** read `selected`, then run `path <lease>` and `lease show <lease>` through `inspect_milkpan` with the deadline. A missing lease or path raises `MetadataUnavailable`.

Milkpan operations are idempotent per spec and scope, so the pending, operation-UUID and group machinery is dropped. A crash between acquire and commit leaves at most an unreferenced commit lease, which the next `commit()` or `reject()` sweeps: it releases consumer-scope leases that no selection references.

### Progress
Stage names change from Saucepan to milkpan. "Reused stored content" is reported only when `fetched` is false, and "downloaded" only when it is true.

### Removal
Delete:
- `saucepan_bootstrap.py`, `saucepan_provider.py` and `saucepan_tool.py`;
- the `saucepan-sdk` dependency, plus `uv.lock` regeneration;
- `tests/saucepan_release_fixture.py`, and the Saucepan-only tests (installer, receipts, migration, setup status).

Rewrite against fixtures:
- the source and bootstrap integration tests use local repositories through `local:` with a real milkpan;
- the managed-binary tests use a loopback HTTP fixture serving release assets.

`POWERSPEC_SAUCEPAN` and `POWERSPEC_SAUCEPAN_CREDENTIAL_FILE` are removed, and the docs say so.

### Test executable
Integration tests need a real milkpan:
- `POWERSPEC_MILKPAN` from the environment when set (CI downloads the pinned release);
- otherwise the managed-binary fixture builds a release-shaped archive around a local milkpan build pointed to by `MILKPAN_TEST_BINARY`;
- otherwise the tests skip with a clear reason.

The CI workflow downloads the pinned release asset and verifies it against the pin.

## Risks / Trade-offs

- [Breaking: old selections are not migrated] → `pspec init` re-selects; docs and the init error for a missing selection say so. The old Saucepan store is untouched, so nothing is lost.
- [Two acquisitions per preparation, candidate then commit] → The second reuses the stored blob, so it costs one local state transition and no download.
- [GitHub-only plus local] → Other hosts fail early with a clear message. Saucepan providers extend this later.
- [Generated policy file] → Owned by Powerspec and rewritten from state. Hand edits are unsupported and documented.
- [The pin must be bumped for every milkpan release Powerspec adopts] → A maintainer script reads the release's `SHA256SUMS` and updates `MILKPAN`. A test asserts that every supported platform has a digest.

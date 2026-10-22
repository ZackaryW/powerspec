# Design

## Context

See `proposal.md` for motivation. The shared `replace_bytes` helper creates a sibling with `tempfile.mkstemp(prefix=f".{target.name}.pspec-", dir=target.parent)`, writes and flushes bytes, calls `os.fsync`, then publishes with `os.replace`. Workset receipts have a 64-character digest plus `.json` beneath the linked worktree's Git administrative directory. Their first write precedes copying the selected change.

Investigation on 2026-10-21 established:

- The installed multi-repository move/copy/retry test fails on both the changed tree and the unchanged pre-implementation baseline. The failure is independent of the completed Saucepan setup change.
- The observed parent exists and is 186 characters long; the destination is 256 characters, but the original staging path is 272 characters. `mkstemp` raises `FileNotFoundError` before publication. Windows `LongPathsEnabled` is 0 on this host.
- In that same parent, a short staging prefix succeeds; the original prefix also succeeds with an extended Windows path. The installed test passes with a shorter diagnostic pytest root and separately with a process-local shim changing only the helper's prefix to `.pspec-` under the ordinary root.
- An unmodified retry reuses the two prepared worktrees but fails again at receipt creation. Source files remain intact and the output workset is not ready. This rules out missing directories, spaces/ampersand quoting, and incorrect Git administrative-directory discovery as the immediate cause.

These are diagnostic experiments, not implementation verification. Ignored local evidence is under `build/workset-investigation/`. Windows' legacy path restrictions and opt-in requirements are documented by [Microsoft](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation).

## Goals / Non-Goals

**Goals:** Remove destination-basename growth from staging while retaining same-filesystem atomic publication and the existing portable helper contract. Verify persistent effects through actual files and the installed CLI.

**Non-Goals:** General Windows path normalization, operating-system policy changes, custom random-name generation, new APIs or dependencies, receipt-key shortening, concurrency redesign, or stronger crash-durability guarantees. Paths whose destination or short staging sibling is itself unsupported remain outside this correction.

## Decisions

### Extend the existing generic writer with a short fixed prefix

Use `.pspec-` as the temporary prefix independent of the target name. Keep `tempfile.mkstemp` responsible for random suffixes and exclusive creation, and keep staging in `target.parent`. A same-directory temporary file keeps `os.replace` on the same filesystem.

Inspected public signatures are `tempfile.mkstemp(suffix=None, prefix=None, dir=None, text=False)` and `os.replace(src, dst, *, src_dir_fd=None, dst_dir_fd=None)`. These existing standard-library APIs supply the needed creation and replacement mechanics. The existing adapter additionally provides byte comparison, flushing, cleanup, and contextual exceptions. Extending it closes the naming gap without replacing those mechanics; third-party package adoption is unnecessary for this bounded correction.

Alternatives: a shorter pytest root only hides the production failure; shortened receipt hashes change persistent identity without fixing other callers; global long-path enablement depends on host policy and application support; adding extended Windows path normalization would broaden compatibility work substantially. None is needed for the confirmed case.

### Portable helper contract and application boundary

`replace_bytes(path: Path, content: bytes) -> bool` remains in `src/powerspec/utils/atomic.py`.

- **Purpose:** Publish complete bytes at a supplied destination. An unrelated application could use the same helper to replace a long-named cache manifest or configuration file.
- **Inputs and results:** The caller supplies the destination and bytes and owns parent creation/validation. Return `True` for a successful write and `False` for identical existing contents. Missing parents and read/write/publication failures retain existing error behavior and contextual `AtomicWriteError` handling.
- **Effects:** Read existing contents; for changed bytes, exclusively create a sibling temporary file, write/flush/fsync, close it, then replace the destination. Unchanged bytes do not create staging files or alter modification time. A publication failure preserves previous destination contents and removes the staging file when cleanup is permitted. Do not expand guarantees for cleanup failure, concurrent writers, or directory durability.
- **Reuse and verification:** Keep the existing helper and its callers. Domain-neutral tests must observe contents, unchanged metadata, preservation on failure, and directory entries after success/failure, rather than merely assert the selected prefix.

Application code continues to select destinations and serialize contents. `workset_transfer.py` retains receipt digests, JSON schema, stage ordering, and retry validation. Configuration, temporary state, syncing, sources, and workset stores continue passing their own paths and bytes. No caller-specific path workaround is planned.

### Verification strategy

1. Add a real-filesystem boundary regression in `tests/test_atomic.py` using a valid long destination for which the old expanded staging basename/path fails. Establish the fixture's validity independently by writing the destination and creating a short sibling. Exercise changed-byte publication and repeat-call behavior. Account for host total-path/component limits with explicit fixture diagnostics; do not assume every OS has Windows' legacy limit. A controlled path-limit simulation can supplement, but cannot replace, the observed native Windows reproduction.
2. Replace old `.config.toml.pspec-*` cleanup globs with directory-content assertions so the new naming convention cannot hide leaks. Exercise publication failure with an existing destination and confirm old bytes and no temporary residue. Retain missing-parent and no-op coverage.
3. Verify workset failure/retry behavior through the real writer and isolated adapter fixtures: fail initial receipt publication, assert preserved source/worktrees and no output registration, then remove the fault and retry. Assert completed receipts still recognize subsequent retries and preserve destination edits, reusing existing tests where they already cover this.
4. Run the installed multi-repository move/copy/retry test under its ordinary pytest root without the diagnostic prefix shim or shorter `--basetemp`. Run affected helper/workset callers, then the full suite because the writer is shared. Preserve isolated registry/environment fixtures. Record host path-policy context with native results; do not alter that policy to get a pass.

## Risks / Trade-offs

- Temporary files lose a readable destination basename → Keep a recognizable short prefix; exclusive random creation supplies uniqueness without embedding destination identity.
- A boundary test can accidentally exercise an invalid destination or an unrelated limit → Prove destination and short-sibling support first and report unsupported fixture conditions explicitly; retain native installed coverage.
- Tests that glob only the old prefix could miss cleanup regressions → Assert actual directory contents.
- Long parent paths may leave insufficient room even for short temporary files → Keep this limitation explicit rather than claiming arbitrary long-path support.

## Migration Plan

Implement and verify the helper slice before application acceptance checks. No data migration or configuration changes are needed: existing receipt filenames, contents, and locations stay intact. A normal code rollback is sufficient, though it restores the original path-length limitation. Do not relocate or delete partial worktrees as part of this correction; the existing retry path reuses them.

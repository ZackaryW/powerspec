# Tasks

## 1. Shared bucket and link reuse

- [x] 1.1 Re-pin milkpan to v0.3.0 with `scripts/pin_milkpan.py` and set `SUPPORTED_LINES = {(0, 3)}`; resolve the home as `MILKPAN_HOME` then `~/.milkpan` and remove `POWERSPEC_MILKPAN_HOME`; verify the pin test, a home-resolution test with a fake home, and that no source or test file mentions `POWERSPEC_MILKPAN_HOME`
- [x] 1.2 Make `ensure_milkpan` reuse any linked milkpan that passes the compatibility check and bootstrap or repoint only when the link is missing or unsupported; rename `manager_state` to `link_state` (`supported`, `unsupported`, `absent`); verify release-fixture tests for reuse of a newer compatible link without download, repointing an unsupported link, bootstrap without a link, and a digest mismatch leaving the link unchanged

## 2. Shared policy and scope names

- [x] 2.1 Replace whole-file policy writing with a marked block (comment markers, outer bytes preserved, `default` rule only when no outer rule covers `default`, malformed markers rejected, full-file validation, atomic replace under the lock, registry in `<home>/powerspec/scopes.json`); verify tests for user rules surviving byte for byte, the `default` rule added and omitted, malformed markers, and repeated writes being idempotent
- [x] 2.2 Rename scopes to `powerspec/manager` and `powerspec/consumer-<hash>[-candidates]` in `milkpan_binary.py` and `sources.py`, and reword the moved-consumer error for selections from an earlier Powerspec; verify the source-store and integration tests with a real milkpan, including plain `milkpan acquire` in `default` still allowed after Powerspec writes its block

## 3. Doctor and force reset

- [x] 3.1 Update doctor's link reporting to `link_state`; verify the doctor tests for supported, unsupported, absent and standalone cases
- [x] 3.2 Add `resetting.py` (`plan_reset`, `apply_reset`: bucket recognition guard, root and home refusal, `~/.powerspec`, the current project's state and lock, error-tolerant deletion with remaining-path reporting) and `pspec doctor --force-reset [--yes] [--json]` (prompt on a TTY, refusal without `--yes` when non-interactive, no other checks in reset mode); verify tests for a confirmed reset, a non-interactive refusal deleting nothing, an unrecognized `MILKPAN_HOME` refused, a home-directory bucket refused, a held file on Windows reported as remaining with exit 1, and JSON output

## 4. Documentation

- [x] 4.1 Update `docs/remote-sources.md` and the README for the shared `~/.milkpan` bucket, link reuse, the managed policy block, `powerspec/` scopes, re-running init after the switch, and `pspec doctor --force-reset` (what it deletes, collateral, the guard); verify every documented variable and flag exists in the code

## Workflow follow-up

- After milkpan v0.3.0 is released: apply, verify, archive (syncing the `managed-milkpan-binary`, `cli-product-surface` and `remote-sources` updates; the sync must handle the RENAMED requirement).

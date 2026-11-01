# Proposal

## Why

Powerspec keeps a private milkpan bucket in `~/.powerspec/milkpan`. Plain `milkpan` use and Powerspec therefore download and store the same commits twice, and run separate copies of milkpan. Powerspec should use the one shared bucket, `~/.milkpan`, which milkpan 0.3.0 adopts as its default home.

Users also need a single, deliberate way to start completely fresh when local state is confused. Today that means hunting down several folders by hand.

## What Changes

- **BREAKING: shared bucket.** Powerspec uses milkpan's own home resolution (`MILKPAN_HOME`, then `~/.milkpan`), shared with plain milkpan use. `POWERSPEC_MILKPAN_HOME` and the private `~/.powerspec/milkpan` bucket are dropped. Consumers selected through the private bucket report "run init", and re-run init once.
- **Reuse, never downgrade:** if `~/.milkpan/links/milkpan` is a milkpan in a release line Powerspec supports, Powerspec uses it as is. It bootstraps or repoints the link (pinned release, verified SHA-256) only when the link is missing or outside the supported line, effective on the next run.
- **Shared policy:**
  - Powerspec manages only a marked block inside the shared `milkpan.toml`, the same managed-section pattern it uses in `openspec/config.yaml`.
  - Rules outside the block are preserved.
  - The block includes a `default` scope rule when no user rule covers `default`, so adding Powerspec rules never disables milkpan's out-of-the-box default.
- **Namespaced scopes:** Powerspec's scopes are `powerspec/manager`, `powerspec/consumer-<hash>` and `powerspec/consumer-<hash>-candidates`.
- **`pspec doctor --force-reset [--yes]`:** a deliberately destructive reset. After confirmation it deletes:
  - the whole shared milkpan bucket, including content other tools put there (accepted by design);
  - all of `~/.powerspec`, including `config.toml` and `worksets.toml`;
  - the current project's `milkpan-state.json`.

  It then reports anything that could not be removed, and the next `pspec init` re-establishes everything. Without `--force-reset`, doctor stays read-only.
- **Spec rename:** the leftover requirement "Remote acquisition uses profile recipes and one Saucepan application" is renamed to name milkpan leases.

## Capabilities

### New Capabilities
<!-- None. -->

### Modified Capabilities
- `managed-milkpan-binary`: shared home, reuse of a compatible shared milkpan, the marked policy block and `powerspec/` scopes.
- `cli-product-surface`: doctor is read-only except for `--force-reset`, the reset behavior, first-use preparation against the shared bucket, and doctor link reporting.
- `remote-sources`: requirement rename only.

## Impact

- **Code:** `milkpan_binary.py` (home, link reuse, policy block, scope names), `sources.py` (scope names), `doctoring.py` and `cli/doctor.py` (`--force-reset`), and a new `resetting.py`.
- **Tests and docs:** the managed-binary, sources, doctor and policy tests; `docs/remote-sources.md` and the README.
- **Depends on:** milkpan's `home-in-dot-milkpan` (v0.3.0). Powerspec re-pins to v0.3.0 and supports release line 0.3.
- **Out of scope:** the old Saucepan store (`~/.saucepan`) stays untouched, even by reset.

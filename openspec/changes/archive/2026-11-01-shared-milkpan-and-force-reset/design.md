# Design

## Context

After `switch-sources-to-milkpan`:
- **`milkpan_binary.py`:**
  - pins milkpan v0.2.0 (`SUPPORTED_LINES = {(0, 2)}`);
  - resolves a private home (`POWERSPEC_MILKPAN_HOME`, else `~/.powerspec/milkpan`);
  - writes the whole `milkpan.toml` from `powerspec-scopes.json` under `powerspec.lock`;
  - names scopes `powerspec-manager` and `consumer-<sha256>[-candidates]`;
  - `ensure_milkpan` repoints the link whenever the manager lease's digest differs from the pin.
- **`sources.py`:** builds the consumer scope as `consumer-<sha256>`.
- **Doctor:** read-only; `managed_state` reports `current`, `behind` or `absent` from the manager lease digest.
- **Managed sections elsewhere:** Powerspec already maintains marked managed sections in `openspec/config.yaml` (`utils/sections.py`).

Milkpan 0.3.0 (`home-in-dot-milkpan`) resolves its home as `--home`, then `MILKPAN_HOME`, then `~/.milkpan`. Milkpan's policy is panned `StaticRules`: any configured rule replaces the built-in `default` rule, and rule scopes match exactly.

## Goals / Non-Goals

**Goals:**
- One bucket for plain milkpan and Powerspec, with no environment variables needed.
- Powerspec never breaks the user's own milkpan setup in normal operation.
- One command that returns the machine to a clean slate.

**Non-Goals:**
- Protecting other tools' content from `--force-reset` (collateral is accepted by design).
- Cleaning the old Saucepan store, or other projects' `milkpan-state.json` files, which reset cannot enumerate.

## Decisions

### Home resolution
`default_home()` returns `MILKPAN_HOME` if set, else `Path.home() / ".milkpan"`, mirroring milkpan exactly. `POWERSPEC_MILKPAN_HOME` is removed and tests switch to `MILKPAN_HOME`. The client already passes `--home` explicitly, so both always agree.

### Link reuse instead of strict pinning
- **Pin:** `MILKPAN` is re-pinned to v0.3.0 with `SUPPORTED_LINES = {(0, 3)}`.
- **`ensure_milkpan`:**
  1. **Override:** `POWERSPEC_MILKPAN`, as before.
  2. **Reuse:** if `links/milkpan/<exe>` exists and `check_compatible` passes (protocol 1 and a supported line), return it, whatever lease or version it came from.
  3. **Bootstrap or repoint:** otherwise, with the link present but incompatible, self-link the pinned release through the existing executable when it can still run; with no link, bootstrap as today. Either way, the switch takes effect on the next run.
- **Doctor:** `manager_state` becomes `link_state` with values `supported`, `unsupported` (the next init switches it) or `absent`, judged by the linked executable's version instead of the lease digest.
- **Why:** this never downgrades a newer compatible milkpan the user installed. Alternative: strict pinning. Rejected, because in a shared bucket it would fight the user's own updates.

### The marked policy block
`milkpan.toml` is TOML, so the markers are comment lines:

```toml
# user rules ...

# >>> powerspec (managed; edits inside this block are replaced) >>>
[[rule]]
scope = "powerspec/manager"
...
# <<< powerspec <<<
```

- **Writing:** `write_policy_block(home, scopes)`:
  1. reads the file;
  2. replaces the text between the markers, or appends the block if it is missing;
  3. leaves every byte outside the markers unchanged;
  4. validates the result by parsing the whole file with `tomllib` and checking each rule's shape;
  5. replaces the file atomically under `<home>/powerspec.lock`.
- **Default rule:** the block includes the `default` allow rule only when no rule outside the block has `scope = "default"`. The check parses the outer text without the block.
- **Errors:** malformed markers (a start without an end, or duplicate blocks) raise `ConfigurationError` naming the file instead of guessing.
- **Consumer registry:** the scope list moves from `powerspec-scopes.json` to `<home>/powerspec/scopes.json`, so Powerspec's files in the shared home sit in one folder.
- **Reuse:** `utils/sections.py` is reused if its marker API fits plain-text comment markers; otherwise a small marker helper goes in `utils/`.

### Scope names
- **Names:** `powerspec/manager`, `powerspec/consumer-<sha256>` and `powerspec/consumer-<sha256>-candidates`. Milkpan scopes are flat names, so `/` is just a character.
- **Old state:** `milkpan-state.json` records its scope. A state file from the private bucket has the old scope name, so lookup reports the existing "consumer moved / run init" path. That message is updated to say "selection from an earlier Powerspec; run init".

### Force reset
`pspec doctor --force-reset [--yes] [--json]` lives in `resetting.py`, as `plan_reset(cwd)` and `apply_reset(plan)`.

**Targets:**
1. the resolved bucket (`MILKPAN_HOME` or `~/.milkpan`);
2. `~/.powerspec`;
3. `<consumer>/openspec/.pspec/milkpan-state.json` and `.lock`, when cwd is inside a consumer.

**Bucket safety guard:** delete the bucket only if it is absent, empty, or contains at least one of `state.json`, `blobs/` or `milkpan.toml`. Never delete the filesystem root, `Path.home()` itself or a path whose resolved form equals either. A refusal deletes nothing at all.

**Confirmation:**
- an interactive TTY prints the targets and asks `Delete these? [y/N]`;
- `--yes` skips the prompt;
- a non-interactive run without `--yes` prints the targets and exits 1.

**Deletion:**
- `shutil.rmtree` with an `onexc` handler that records failures (Windows in-use files) and continues;
- a read-only attribute is cleared and the deletion retried once.

**Result:**
- removed and remaining paths, as human text or JSON (`{"reset": {"removed": [...], "remaining": [...]}}`);
- exit 0 only when nothing remains;
- no other doctor checks run in reset mode;
- the human output ends with "Run pspec init to re-establish".

### Migration of the private bucket
Nothing is migrated. `~/.powerspec/milkpan` is left for the user (or removed by `--force-reset`). The docs say so.

## Risks / Trade-offs

- [Reset deletes other tools' bucket content and all Powerspec configuration] → By design. The confirmation lists everything first.
- [`MILKPAN_HOME` pointed somewhere surprising] → The bucket recognition guard refuses unrecognized, non-empty directories.
- [A user hand-edits inside the managed block] → Their edits are replaced, as the marker comment says. Rules outside the block are theirs.
- [A user defines their own `default` rules] → Powerspec stops adding its `default` rule, and their policy governs `default`.
- [Two Powerspec processes rewrite the block] → The block is rewritten under `powerspec.lock`, and the policy file is replaced atomically.

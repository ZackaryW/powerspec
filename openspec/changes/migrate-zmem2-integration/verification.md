# Verification

## Runtime migration checkpoint

On 2026-10-22, built the clean zmem2 revision
`b14d257911270565dcb6228da435520ef79cf506` under Node 26.12.1.
All 75 upstream tests passed. The packed zmem2 0.1.0 archive has SHA256
`0ee1ffe72324d5a5c47f365bf93a25520928187bd62764725db8b32fa1fe686a`.
An isolated npm installation passed version/help checks, initialized a disposable
repository, recalled its decision annotation and accepted a proposed commit.

Evidence and rollback material are under
`~/.tmp/ps-zmem2-migration-20261022/`. Both predecessor uv tool environments
were copied and hash-verified (84 and 292 files) before their owner-specific uv
uninstall commands removed their launchers. All 58 pre-existing files beneath
the legacy user data/runtime home retained their hashes after the switch.

The new package is installed with npm's explicit Windows prefix `~/.local/bin`:
its runtime lives in `~/.local/bin/node_modules/zmem2`, and its npm-generated
PowerShell/CMD launchers are on the existing PATH. Both a fresh PowerShell process
and Python subprocess execution using `shutil.which('zmem')` returned version
0.1.0. A direct Windows CreateProcess call does not resolve npm CMD launchers
without the extension; resolve the executable first, as with other npm tools.

The first global installation at Scoop's default prefix was removed. Invoking
that installation through Scoop's junction returned no output, while using its
canonical path worked. The upstream entrypoint compares import.meta.url with
the uncanonicalized argv path. The explicit non-junction prefix avoids this
without modifying upstream code or changing PATH order.

Powerspec initialization created only `.zmem/config.yaml` and `.zmem/.gitignore`
as trackable repository setup; generated `/index/` remains ignored. Initial
recall returned computed decisions with a 64-commit/400-annotation window,
47 observed nodes and incomplete full-history coverage. One existing effect
points outside that window and reports `incomplete_history`. This is bounded
verification, not a claim that all historical effects were verified. Acceptance
calls used `--no-background`; no persistent background policy was changed.

## Runtime rollback

Preserved environment roots are `legacy/scoop-tool` and `legacy/roaming-tool`
under the evidence directory. Their original locations and entrypoints remain in
their `uv-receipt.toml` files; launcher copies are beside those directories.
The primary predecessor was installed from zmem Git revision
`86f86274be6c89bce85e40d6c0217cb52da45918`; the older installation referenced a
local F: checkout and therefore also has a complete environment backup.

To restore the predecessor, uninstall only the new package with
`npm uninstall --global --prefix "$HOME/.local/bin" zmem2`, restore the chosen
saved tool environment to its exact original location, and restore its saved
launcher to the original receipt path. Verify normal command resolution after
restoration. Do not delete either product's data or copy generated indexes
between environments. The verified tarball remains available to reinstall zmem2.

## Integration checkpoint

The runtime/planning commit is `0412ba6`. Its proposed message passed zmem check
with `ok=true`, no diagnostics and complete 111-commit attention. Post-commit
show succeeded with complete 112-commit coverage and no annotations.

Observed red results for the previous repository origin and absent runtime
guidance before changing the bundled resources. Focused composition, guidance,
doctor, installation and native migration tests then passed: 29 passed, 1 skipped.
The native test uses real Saucepan and ZuAT with isolated local origins, home and
registry. It verifies distinct recipe selection, retained predecessor outputs,
unchanged matching skill bytes/mtime, intact owned updates, preserved edits on
failure, successful retry after the fixture owner restores its edit, and unchanged
hook bytes. A test assertion initially used the wrong SourceBinding field name;
correcting it required no production change.

`uv build --wheel` succeeded. Inspection of the built wheel verified the zmem2
origin, stable alias/user scope and runtime guidance in packaged resources.
No source acquisition or provisioning code needed modification.

## Installed consumer acceptance

Installed the verified Powerspec 0.1.6 wheel through uv. The first ordinary
`pspec init --agent codex` acquired zmem2 but preserved three conflicting memory
skills and reported a stale hook receipt. Complete ZuAT inspection proved all
three owned skills exactly matched the acquired zmem2 source, while their
ownership baselines still represented the predecessor. Hook contents also
matched the intended dispatcher.

Reconciled only those three source-matching owned skills with ZuAT's recoverable
update API and repaired the matching hook receipt through the guarded hook API.
Each operation reported `native_changed=false`; all 11 recorded memory-skill and
hook file hashes remained unchanged. No conflicting content was overwritten,
no automatic skill-repair behavior was added, and no blanket force initialization
was used. The retry succeeded, reusing all 22 selected skills and the hook group.
The initial run also updated intact owned OpenSpec skills from the installed
bundle through the existing provisioning path.

The consumer now pins zmem2 revision
`b14d257911270565dcb6228da435520ef79cf506`, matching the installed runtime build.
All predecessor source selections remain unchanged. `pspec sync` published the
new standing memory guidance; both startup and compaction resolver outputs
include its intended-runtime and installation-boundary instructions. Doctor
returned `ok=true`. Its warnings correctly leave source readiness unchecked by
that command and host enablement, delivery receipts and adherence unverified;
source provenance was separately verified through the retained selection.

Evidence includes `live-inspection.json`, `live-repair.json`,
`consumer-init-retry.log`, before/after source snapshots, the two hook outputs and
`consumer-doctor.json` in the external evidence directory. A duplicated ignore
entry emitted by initialization was removed without changing ignore semantics.

## Final validation

The complete Powerspec pytest suite passed: **634 passed, 11 skipped** in
330.12 seconds. Native Saucepan tests used the verified v0.11.0 raw manager and
release assets; installed acceptance used the updated global pspec executable.
The log is `full-suite.log` in the evidence directory. Upstream zmem2 remains
verified by its earlier 75 passing tests; no upstream code changed afterward.

Strict OpenSpec validation and `git diff --check` passed. Both predecessor and
zmem2 retained selections were independently resolved and their outputs remain
available. The integration checkpoint `83f3b5c` passed zmem validation; its
post-commit inspection reported complete 113-commit coverage with no annotations.
The new change remains active for separately requested spec synchronization and
archive. No release, tag or push was performed.

At the user's request, removed the standalone migration guide and its links.
Keep machine-specific setup and rollback evidence in this change; initialization
documentation retains only the source-selection order and runtime boundary.
This documentation-only adjustment does not change the tested behavior.

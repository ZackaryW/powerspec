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

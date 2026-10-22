# Using zmem2 with Powerspec

The bundled `@builtin/zmem-lifecycle` profile selects the three memory skills
from [ZackaryW/zmem2](https://github.com/ZackaryW/zmem2) at `main`. The source alias
remains `zmem`, the selector remains `zmem/skills/*`, and native skill names and
user scope are unchanged. Excluding the profile removes its skill and guidance
selection, not shared user installations.

## Install and identify the runtime

Skill provisioning and runtime installation are separate. Powerspec installs
guidance through ZuAT; it does not install a zmem executable. The intended npm
package is `zmem2`, but its command is **`zmem`**, also used by the Python
predecessor. Check the resolved executable, version and command surface:

```powershell
Get-Command zmem -All
zmem --version
zmem --help
```

The new CLI exposes `init`, `sync`, `recall` and `check --file` / `check --stdin`.
A successful service probe or the executable name alone does not identify it.
Node 24 or 26 and Git are required by the current upstream package.

Follow the upstream build/install contract from a clean, selected revision:

```powershell
npm ci
npm test
npm pack
npm install --global ./zmem2-0.1.0.tgz
```

Inspect existing installations before replacing commands. On Windows, verify
the resulting command from a fresh shell. With the current zmem2 0.1.0 entrypoint,
Scoop's junction-backed default npm prefix can exit silently: calling through a
junction fails the entrypoint's path comparison. A non-junction prefix already
on PATH avoids this, for example on machines with `~/.local/bin` on PATH:

```powershell
npm install --global --prefix "$HOME/.local/bin" ./zmem2-0.1.0.tgz
```

Remove a superseded npm installation from its original prefix if it still
shadows the selected installation. For legacy uv commands, retain installation
metadata and backups, then use the owning uv installation's uninstall operation.
Multiple uv roots can expose separate launchers; removing one need not remove
the other. Do not overwrite unknown executables. Python subprocess callers on
Windows should resolve the npm CMD launcher with `shutil.which('zmem')` before
invoking it. Verify JSON output as well as exit status.

## Move an existing Powerspec consumer

After installing the updated Powerspec distribution, run from the consumer:

```powershell
pspec init --agent codex
pspec sync
```

Use the explicit agent you actually use. The new origin is a distinct recipe,
so initialization acquires its first selection even when the predecessor has a
warm cache. Ordinary init does not refresh other existing selections. Retained
predecessor outputs remain available; do not delete Saucepan state to migrate.

Initialize before `pspec upgrade`: upgrade first looks up the currently declared
recipe, which cannot succeed until this consumer has selected the new origin.
Once initialized, ordinary upgrade refreshes the new recipe normally.

Matching native skills are reused, intact owned skills may update, and modified
or ambiguous targets remain conflicts. An origin change grants no overwrite
authority. Preserve local edits and resolve ownership diagnostics explicitly;
`init --force` does not replace edited skills. Existing hook registrations stay
under the same ownership contract. Sync publishes the new standing guidance;
it does not install or switch runtimes.

## Initialize and verify memory

With the new executable selected, use its normal repository lifecycle:

```powershell
zmem init .
zmem recall --event DECISION --limit 10
zmem check --file COMMIT_EDITMSG
```

The message file must contain the proposed commit text. Repository initialization
creates missing `.zmem/config.yaml` and a nested `.zmem/.gitignore` for `/index/`;
configuration remains trackable. Preserve existing configuration and extension
trust choices. Queries can compute missing state and normally admit background
backfill; `--no-background` suppresses that admission for a verification call.
Report `memory_coverage`, attention limits and diagnostics separately from
whether the command succeeded. A bounded empty result is not proof that no older
memory exists.

## Preserve data and rollback

The new engine rebuilds computed memory from Git. Its user storage is versioned
under `~/.zmem/v2`, or the explicitly selected `--home`/`ZMEM_HOME`; repository
indexes are environment-scoped beneath `.zmem/index`. It does not migrate old
databases or Python extensions. Do not delete predecessor databases, runtime
directories or configuration during a command switch.

Record the selected package revision/hash, previous package-manager receipts,
original launcher locations and backup paths. Rollback restores the predecessor
installation and command selection against its preserved data. Keep the new
engine's data separate rather than copying indexes into the predecessor. A
Powerspec rollback restores the previous profile/package and retained source
recipe; it does not require erasing either source's retained outputs.

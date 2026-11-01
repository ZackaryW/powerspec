# Remote sources

Powerspec delegates Git acquisition and retained materialization to [milkpan](https://github.com/ZackaryW/milkpan), a small resource bucket. Profiles declare friendly aliases and exact Git recipes. Powerspec does not clone repositories or keep a separate user-level source registry.

Ordinary `pspec init` reuses an existing consumer's retained selection without fetching, regardless of age. When a consumer needs a new selection, Powerspec resolves the recipe's reference at most once per day for that consumer. Within that day it reuses the resolution offline; content already stored for the resolved commit is never downloaded again, even for another consumer. Explicit `pspec init --force` or `pspec upgrade --agent <agent>` resolves again immediately. Each consumer holds its own selection, so refreshing one does not change another's selected revision.

## Supported origins

| Recipe origin | Fetched through |
| --- | --- |
| `https://github.com/<owner>/<repo>` (optionally `.git`) | milkpan's GitHub provider: a snapshot of the commit, without history |
| an absolute local path, or a `file://` URL | milkpan's local provider: the repository's committed files at the commit (needs `git`) |

Other origins (GitLab, SSH URLs, other hosts) fail before milkpan is called, with an error naming the supported forms. GitHub requests use `GH_TOKEN`, `GITHUB_TOKEN` or `gh auth token` when available, and are anonymous otherwise.

## Managed milkpan

Powerspec shares milkpan's own bucket: `MILKPAN_HOME` if set, otherwise `~/.milkpan`, the same place plain `milkpan` uses. A commit fetched by either is stored once. Powerspec never touches a Saucepan installation.

- **Reuse:** if `~/.milkpan/links/milkpan` is a milkpan that speaks protocol 1 in a release line Powerspec supports (currently 0.3), Powerspec uses it as is, even when it is newer than Powerspec's pin. It never downgrades your milkpan.
- **First preparation:** when no usable link exists, an authorized source-materializing operation (init, init --force, upgrade, or sync preparing a missing source) downloads the pinned milkpan release asset for this platform. Powerspec verifies it against the SHA-256 pinned in `milkpan_binary.py` and extracts it outside the bucket. It then uses that binary once to acquire milkpan's own release in scope `powerspec/manager` and link it as `~/.milkpan/links/milkpan`.
- **Later runs:** they use the link and need no network.
- **Updates:** when a Powerspec release supports only a newer release line than the linked milkpan, the next preparation or upgrade links the pinned release, through the old milkpan itself when it still runs. Programs already running keep their version; the next run uses the new one.
- **Read-only operations:** status, doctor, sync of already selected sources, hooks and skill metadata lookup never download, link or update milkpan. They report it as unavailable when it is missing.
- **Override:** `POWERSPEC_MILKPAN` selects a standalone executable. Powerspec checks its protocol (1) and release line (0.3) but never links, updates or adopts it.
- **Doctor:** reports executable compatibility, whether the shared link is in a supported release line (or standalone mode), and uninspected selected-source readiness separately.

### The policy file

The shared `~/.milkpan/milkpan.toml` belongs to you. Powerspec manages only the block between these marker lines and preserves everything else:

```text
# >>> powerspec (managed; edits inside this block are replaced) >>>
...
# <<< powerspec <<<
```

The block allows:
- scope `powerspec/manager` to manage milkpan's own release;
- each consumer's `powerspec/consumer-<hash>` scope and its `-candidates` scope to acquire, reacquire, read and release `github:` and `local:` sources;
- scope `default` for every lease operation, but only when no rule of yours covers `default`. Any configured rule replaces milkpan's built-in default, so this keeps plain `milkpan` working.

Consumer leases carry a lease obligation that keeps selected content from expiring. Candidate leases refresh daily. Powerspec's own files in the bucket live under `~/.milkpan/powerspec/`.

### Starting over

`pspec doctor --force-reset` lists what it will delete and, after confirmation (`--yes`, or an interactive yes), removes:
- the whole milkpan bucket, **including content other tools stored there**;
- all of `~/.powerspec`, including `config.toml` and `worksets.toml`;
- the current project's `milkpan-state.json`.

It reports anything it could not remove, for example files of a still-running milkpan on Windows, and exits nonzero in that case. Run `pspec init` afterwards to re-establish everything. Other projects' selections then report "run init". Reset refuses, and deletes nothing, when `MILKPAN_HOME` points at a directory that is not recognizably a milkpan bucket, a filesystem root or your home directory. It never touches a Saucepan store. Without `--force-reset`, doctor only inspects.

## Profile recipes and selections

The first segment in `<identity>/<selector>` is a profile-owned source alias. The same effective profile graph declares its recipe:

```toml
skills = ["zmem/skills/*"]

[[source]]
id = "zmem"
provider = "git"
origin = "https://github.com/ZackaryW/zmem2"
reference = "main"
```

Identical declarations can be shared across selected profiles. Different recipes for the same alias are a composition error. `builtin` remains reserved.

Each canonical owning `openspec/.pspec/config.toml` has its own milkpan scope (`powerspec/consumer-<hash>`). Preparing a recipe takes two steps:

1. **Resolve:** the reference is resolved in the consumer's candidate scope, which caches the resolution for a day.
2. **Select:** the resulting exact commit is leased in the consumer's scope.

That commit lease's content path never changes, and its content is shared with every other lease on the same commit. Aliases with identical recipes share the selection. `pspec init` prepares missing selections, and repeated init reuses them without refresh. `pspec sync`, status and hooks only inspect them. A missing required selection is an error suggesting init; lookup never repairs it.

Installation and explicit upgrade retain:

- the Powerspec alias and the milkpan spec (for example `github:zackaryw/zmem2`);
- the recorded repository origin and requested Git reference;
- the resolved Git revision and the commit lease ID;
- the content directory milkpan returns for that lease.

Milkpan stores a complete snapshot before Powerspec applies a profile's path selector. A selector such as `skills/*` therefore controls which resources participate in composition and installation; it does not reduce network transfer.

## Lifecycle boundaries

Recipe declaration, materialization, selection, installation, synchronization and upgrade are separate actions:

- profiles own aliases and exact source recipes;
- Powerspec owns its managed milkpan and policy, and validates selected materializations;
- milkpan owns source acquisition and stored content;
- ZuAT owns native agent installation and installation provenance;
- `pspec sync` reuses existing selections without refresh and does not install or remove skills;
- ordinary `pspec init` may acquire a selected recipe only when it is missing;
- explicit upgrade and `pspec init --force` refresh existing selected recipes;
- a consumer's first selection of a recipe is published once it validates, before agent provisioning, so a skill conflict cannot leave upgrade or sync without a selection. A refreshed replacement of an existing selection is still published only when the whole init or upgrade succeeds, and the replaced commit lease is released only after that.

Unavailable milkpan during read-only lookup, a missing selection or lease, a failed acquisition or an invalid replacement produces a source-specific diagnostic. Such a failure does not turn an earlier valid binding into a successful replacement.

## Reusable catalogs and direct skills

Reusable catalogs are discovered from `.pspec` directories inside the materialized repository. A repository may publish nested catalogs, whose resources share the registered source namespace. `openspec/.pspec` is always private consumer configuration and is excluded. Discovery validates all published declarations and rejects duplicate identities before a replacement binding becomes visible. A missing reusable catalog cancels that registration attempt.

Direct skill references do not require `.pspec`. Their selectors are source-relative:

- `tools/skills/example` selects that one skill root;
- `tools/skills/*` selects immediate child skill roots;
- `tools/skills/**` explicitly selects skill roots recursively.

Only directories containing `SKILL.md` participate. Selected declarations are validated together, ordered by source-relative path, and retain the complete skill directory. Absolute paths, parent traversal, canonical or symlink escapes, empty initial matches, and duplicate selected declared names are errors. The installed name comes from `SKILL.md`, not the source identity or folder name.

Conceptually, explicit reusable discovery follows this boundary:

```python
recipe = {"provider": "git", "origin": "https://github.com/team/tools", "reference": "main"}
store = MilkpanSources(consumer_path=Path("openspec/.pspec/config.toml"))
binding = store.ensure("team-tools", recipe)
catalogs = ExternalCatalogs().register(binding)
catalog = Catalog(sources=catalogs.sources(), gitsources={"team-tools": binding})
store.commit()  # Only after all required caller validation succeeds.
```

The registration step only validates and exposes resources. It does not provision a skill.

## Upgrade success boundary

Run `pspec upgrade --agent <agent>` from inside the owning Git repository. Add `--force` only when selected unowned or locally modified skill targets should be archived and replaced through ZuAT. Upgrade brings the managed milkpan to the pinned release (effective on the next run), then processes every remote skill selector in the consumer's effective profile bundle:

1. resolve the previously materialized selections without fetching;
2. refresh every referenced profile recipe through milkpan;
3. validate all replacement selectors and target collisions;
4. reconcile every selected bundled, local, and refreshed skill through ZuAT;
5. reconcile the generic hook dispatcher for the target agent;
6. identify obsolete copies only from the prior verified remote selection and current ZuAT ownership;
7. publish the validated retained source selection locally; publication failure prevents removal;
8. submit all obsolete copies in one recoverable ZuAT removal operation;
9. verify their absence before reporting success.

No removal begins until all refresh, validation, collision, skill provisioning, and hook reconciliation work succeeds. A failed or unknown source does not establish absence. An empty replacement is accepted only for a selector that previously resolved successfully.

If removal or final verification fails, Powerspec asks ZuAT to restore the removal operation's complete before-state. The command reports failure after successful restoration and reports a partial result if ZuAT cannot restore it. The published source selection, stored content and already completed non-removal updates are outside this rollback boundary. A removal failure reports that the new source selection was already published.

Milkpan does not report source deregistration. Unavailable milkpan or a missing selection therefore remains an error and preserves installed copies; Powerspec does not infer an intentional deletion from that error.

## Retention and recovery

The gitignored `openspec/.pspec/milkpan-state.json` stores this consumer's selected commit leases, never credentials. Lookup checks that the lease still exists in the consumer's scope at the recorded commit, and uses the content path milkpan returns. Updating a shared source does not move another consumer's selection.

Candidates become selected only after validation and, for agent installation, successful provisioning. A rejected candidate's lease is released unless a selection uses it. Milkpan operations are idempotent per spec and scope, so retrying a failed preparation reuses the same leases; there is no pending operation to reconcile.

Save the state file before rebinding a moved or copied consumer: its recorded canonical identity intentionally rejects silent scope reuse. Remove `milkpan-state.json` and run init to establish the new scope.

Mutations serialize through `milkpan-state.lock`. If a process crashes, confirm its recorded PID is no longer running before removing that lock and retrying.

**Switching from an earlier Powerspec.** Selections made in the earlier private bucket (`~/.powerspec/milkpan`) are not reused: run `pspec init` once, and delete that folder (or run `pspec doctor --force-reset`). **From Saucepan:** earlier Powerspec versions used Saucepan and `saucepan-state.json`. This version ignores both and leaves the old Saucepan store untouched. Run `pspec init` once per consumer to select its sources through milkpan; afterwards the old store and state file can be deleted. `POWERSPEC_SAUCEPAN` and `POWERSPEC_SAUCEPAN_CREDENTIAL_FILE` are no longer read; use `POWERSPEC_MILKPAN` for a standalone executable.

With an explicit agent, forced initialization can repair a stale hook ownership receipt only when the uniquely identified native group already matches Powerspec's desired content. ZuAT rechecks equality during its receipt-only update, preserving native bytes and modification time. Edited or ambiguous hooks still fail; recovery operation identifiers are reported. Source-only initialization performs no hook work. Forced initialization with an agent also recoverably replaces completely inspected conflicting selected skills. Upgrade keeps its separate `--repair-hooks` option and its skill-only `--force` meaning.

## Resolve-only remote selections

Authored profiles may use `resolve-skills = ["tools/skills/*"]` with the same `[[source]]` recipe as installation selections. Init prepares those selected sources and upgrade refreshes them, without creating native targets for resolve-only resources. Runtime lookup, hooks, and status remain read-only. Removing resolve-only declarations or moving an installation declaration into that list does not establish obsolete-copy removal evidence. Only current installation contributions participate in that evidence.

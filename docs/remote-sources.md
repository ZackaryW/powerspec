# Remote sources

Powerspec delegates Git acquisition and retained materialization to Saucepan. Profiles declare friendly aliases and exact Git recipes; Powerspec does not clone repositories or keep a separate user-level source registry.

## Managed Saucepan executable

Powerspec uses Zuu's managed-release lifecycle when an authorized init or upgrade needs the default Saucepan client. Read-only lookup only inspects an already installed compatible executable. If Powerspec's shared executable under `~/.saucepan/bin` is absent, Powerspec selects an official Saucepan 0.10 GitHub release for the current platform, extracts only the exact manager member from the platform ZIP, validates `--version` and required commands on a staged file, and publishes it atomically. These are the verified CLI protocol lines supported by the installed SDK boundary. Set `POWERSPEC_SAUCEPAN` to select an explicit manager path. An explicitly supplied SDK client bypasses this lifecycle.

Successful release checks are cached for 24 hours. A fresh matching check avoids GitHub discovery. When a later discovery or upgrade fails, Zuu retains a compatible installed executable; when no compatible executable can be produced, Powerspec reports the managed-tool failure before attempting the source operation. Constructing a catalog or running a bundled-only profile does not trigger installation: the lifecycle is lazy until a selected Git recipe needs materialization.

## Profile recipe and Saucepan application contract

The first segment in `<identity>/<selector>` is a profile-owned source alias. The same effective profile graph declares its recipe:

```toml
skills = ["zmem/skills/*"]

[[source]]
id = "zmem"
provider = "git"
origin = "https://github.com/ZackaryW/zmem"
reference = "main"
```

Identical declarations can be shared across selected profiles. Different recipes for the same alias are a composition error. `builtin` remains reserved.

All recipes use one stable application registration key `powerspec` and its returned
UUID. Each canonical owning `openspec/.pspec/config.toml` has a separate explicit
scope; aliases with identical recipes share its selected output. `pspec init`
registers missing intent and prepares a pinned generation. Repeated init reuses
that selection without refresh. `pspec sync`, status and hooks only inspect it.
A missing required selection is an error suggesting init; lookup never repairs it.

The current SDK is pinned to source commit `8a2d04e7d2e393c035715520254bdd5955651873`.
SDK package version 0.2.0 and manager protocol 0.10 are separate version contracts.
Local administrative registration creates source and immutable policy definitions;
resource acquisition, policy adoption, group preparation and retention checks use
the bound application context. Denials never trigger an unrestricted retry.
Set `POWERSPEC_SAUCEPAN_CREDENTIAL_FILE` for an explicitly protected application;
default registration requires no credential and no OS keyring.

Saucepan expands its `explicit-update` policy profile when Powerspec prepares a
missing source or an explicit upgrade. Powerspec registers those flat immutable
policies and adopts their UUID references. This means fresh source retrieval,
manual copied-result updates and the profile's managed revision settings; upgrade
explicitly overrides copied-result updates to `always`. The Rust manager owns
these defaults. Powerspec's authored profiles still own source aliases and skill
selection, and are a separate concept from Saucepan policy profiles.

Pinned retention and consumer scope remain explicit Powerspec choices. Policy
profiles do not enable credentials, keyring integrity, or managed app installation.
Lookup and repeated init use the selected receipt without expanding a profile.

Installation and explicit upgrade submit the profile's Git origin and reference, request the complete repository, and retain:

- the Powerspec alias and Saucepan canonical source ID;
- the recorded repository origin and requested Git reference;
- the resolved Git revision and artifact ID;
- the verified managed directory returned by Saucepan.

Saucepan performs a full repository acquisition before Powerspec applies a profile's path selector. A selector such as `skills/*` therefore controls which resources participate in composition and installation; it does not reduce Git network transfer.

## Lifecycle boundaries

Recipe declaration, materialization, selection, installation, synchronization, and upgrade are separate actions:

- profiles own aliases and exact source recipes;
- Powerspec owns the single Saucepan application lifecycle and validates selected materializations;
- Saucepan owns source acquisition and retained content;
- ZuAT owns native agent installation and installation provenance.
- `pspec sync` reuses existing materializations without refresh and does not install or remove skills.
- `pspec init` may acquire a selected recipe only when it is missing;
- explicit upgrade is the only Powerspec operation that refreshes an existing selected recipe.

An unavailable Powerspec app during read-only lookup, ambiguous matching source, missing full-root artifact, failed acquisition, or invalid replacement produces a source-specific diagnostic. Such failure does not turn an earlier valid binding into a successful replacement.

## Reusable catalogs and direct skills

Reusable catalogs are discovered from `.pspec` directories inside the materialized repository. A repository may publish nested catalogs, whose resources share the registered source namespace. `openspec/.pspec` is always private consumer configuration and is excluded. Discovery validates all published declarations and rejects duplicate identities before a replacement binding becomes visible. A missing reusable catalog cancels that registration attempt.

Direct skill references do not require `.pspec`. Their selectors are source-relative:

- `tools/skills/example` selects that one skill root;
- `tools/skills/*` selects immediate child skill roots;
- `tools/skills/**` explicitly selects skill roots recursively.

Only directories containing `SKILL.md` participate. Selected declarations are validated together, ordered by source-relative path, and retain the complete skill directory. Absolute paths, parent traversal, canonical or symlink escapes, empty initial matches, and duplicate selected declared names are errors. The installed name comes from `SKILL.md`, not the source identity or folder name.

Conceptually, explicit reusable discovery follows this boundary:

```python
recipe = {"provider": "git", "origin": "https://example.test/team/tools", "reference": "main"}
store = SaucepanSources(consumer_path=Path("openspec/.pspec/config.toml"))
binding = store.ensure("team-tools", recipe)
catalogs = ExternalCatalogs().register(binding)
catalog = Catalog(sources=catalogs.sources(), gitsources={"team-tools": binding})
store.commit()  # Only after all required caller validation succeeds.
```

The registration step only validates and exposes resources. It does not provision a skill.

## Upgrade success boundary

Run `pspec upgrade --agent <agent>` from inside the owning Git repository. Add `--force` only when selected unowned or locally modified skill targets should be archived and replaced through ZuAT. Upgrade processes every remote skill selector in the consumer's effective profile bundle:

1. resolve the previously materialized selections without fetching;
2. refresh every referenced profile recipe through the Powerspec Saucepan app;
3. validate all replacement selectors and target collisions;
4. reconcile every selected bundled, local, and refreshed skill through ZuAT;
5. reconcile the generic hook dispatcher for the target agent;
6. identify obsolete copies only from the prior verified remote selection and current ZuAT ownership;
7. publish the validated retained source selection locally; publication failure prevents removal;
8. submit all obsolete copies in one recoverable ZuAT removal operation;
9. verify their absence before reporting success.

No removal begins until all refresh, validation, collision, skill provisioning, and hook reconciliation work succeeds. A failed or unknown source does not establish absence. An empty replacement is accepted only for a selector that previously resolved successfully.

If removal or final verification fails, Powerspec asks ZuAT to restore the removal operation's complete before-state. The command reports failure after successful restoration and reports a partial result if ZuAT cannot restore it. The published source selection, source caches and already completed non-removal updates are outside this rollback boundary. A removal failure reports that the new source selection was already published.

Saucepan's current public API does not expose source deregistration evidence. An unavailable Powerspec app or missing materialization therefore remains an error and preserves installed copies; Powerspec does not infer an intentional deletion from that error.

## Retention and recovery

On first use of the default `~/.saucepan/bin` manager, PowerSpec stages and
validates the executable outside the store, initializes the store through
Saucepan, then publishes the manager and its release-check cache. This keeps
installer files from making a fresh store look like an incompatible nonempty
directory. Explicit executable destinations outside the default path retain
their existing installation behavior.

If a previous failed install left only the manager and/or `saucepan-check.json`
under `~/.saucepan/bin`, PowerSpec validates any existing manager and preserves
that directory in a sibling `.powerspec-saucepan-backup-*` before initialization.
Backups remain after success or failure; failures report the backup path. Keep
them until you have confirmed recovery. Unknown files, linked paths and existing
store data are not automatically relocated. Saucepan owns validation and recovery
of its interrupted initialization metadata.

Default provisioning uses the sibling `.powerspec-saucepan-bootstrap.lock` to
exclude concurrent PowerSpec bootstraps. If the process crashes, confirm the PID
recorded in that lock has stopped before removing that specific stale lock.
Rerun `pspec init` with the original options after fixing a failed setup;
`upgrade` requires the initial source selection and does not substitute for init.

The gitignored `openspec/.pspec/saucepan-state.json` stores this consumer's selected
receipts and pending operation identities, never credentials. Lookup validates the
manager's authenticated pin receipt and uses its returned path; it does not follow
a moving claim or reconstruct store directories. Updating a shared source does not
move another consumer's selection.

Candidates become selected only after validation and, for agent installation,
successful provisioning. Explicit upgrades adopt new immutable policy UUIDs before
preparing the replacement. A lost preparation response retains its original group,
revision, expanded policy catalog, UUID references and pin registration key for
reconciliation on retry. The retry uses these saved inputs without expanding the
named policy profile again. Known rejected
candidates can be abandoned while their pins remain retained, allowing a later
upgrade to fetch a corrected revision.

Historical and rejected generation pins are deliberately retained. This prevents
reclamation racing read-only readers. Cleanup must be explicit, reader-safe and
limited to the owning consumer's receipts; Powerspec never automatically unpins.
Save the receipt file before rebinding a moved/copied consumer: its recorded
canonical identity intentionally rejects silent scope reuse. Start fresh local state
and run init to establish the new scope. The old receipts remain cleanup evidence.

Mutations serialize through `saucepan-state.lock`. If a process crashes, confirm its
recorded PID is no longer running before removing that lock and retrying the same
operation. Never delete pending receipts to retry an uncertain mutation.

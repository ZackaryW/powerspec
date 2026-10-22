# Remote sources

Powerspec delegates Git acquisition and retained materialization to Saucepan. Profiles declare friendly aliases and exact Git recipes; Powerspec does not clone repositories or keep a separate user-level source registry.

Ordinary `pspec init` reuses an existing consumer's exact retained selection without fetching, regardless of age. When a new folder needs its own selection, Saucepan may reuse valid shared retrieval material younger than **24 hours**. At 24 hours, or when material is missing, it retrieves upstream again. Cache age comes from the provider's retrieval evidence; initializing another folder does not restart the clock. Recent cached material works offline, but an expired cache requires successful retrieval rather than silent stale fallback. Explicit `pspec upgrade --agent <agent>` refreshes immediately. Each consumer retains its own pins, so refreshing one does not change another's selected revision.

## Managed Saucepan executable

Powerspec uses Saucepan's official managed setup when an authorized source-materializing operation needs a missing default installation at `~/.saucepan/bin/saucepan` (`saucepan.exe` on Windows). It downloads the **v0.11.0** installer, verifies its pinned SHA256, and runs it outside the store with an explicit operation UUID. Saucepan owns initialization, managed launcher publication, receipts and recovery. First setup requires PowerShell 5.1+/.NET on Windows, or POSIX sh, curl, unzip, standard utilities and sha256sum/shasum on Unix. Powerspec never bypasses execution policy.

Existing default installations must pass both a bounded version probe and `setup-status`: only compatible, ready ownership is accepted. Reuse performs no release discovery, manager replacement or self-update. Old `saucepan-check.json` files are ignored and left untouched. `pspec upgrade` refreshes selected sources and agent assets only. A shared manager version change is an explicit provider action: `saucepan --root ROOT self-update APP CLAIM --tag v0.11.0 --operation UUID` using identities from `setup-status`.

`POWERSPEC_SAUCEPAN` explicitly selects a standalone executable, even if it names the shared path. Powerspec checks its protocol but never installs, updates or adopts that file. An injected SDK client bypasses manager provisioning. Bundled-only operations do not create a Saucepan client. Status, doctor, sync, hooks and skill metadata lookup never run the installer. Doctor reports executable compatibility, managed state (or standalone mode), and uninspected selected-source readiness separately.

The production descriptor pins both official installer hashes and the SDK revision in `saucepan_provider.py`. Its explicit loopback fixture descriptor is test-only; ambient environment variables cannot redirect installation downloads. The managed SDK client uses the inspected default root explicitly; an unrelated `SAUCEPAN_ROOT` cannot redirect it. Standalone clients retain the SDK's root selection.

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

The current SDK is pinned to source commit `324282bac14fd0e0032a07e0fbed85ee95447dbb`.
SDK package version 0.3.0 and manager protocol 0.11 (standalone 0.10 remains supported) are separate version contracts.
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

First setup prints its root and operation UUID to stderr. A complete result is reinspected before source access. Noncomplete receipts preserve status, backup paths and durable retry-shim identity. Timeout, malformed output and response loss are uncertain outcomes: inspect the original provider operation **before rerunning init**. Powerspec does not automatically retry setup. Use an external setup-capable manager if the shared launcher is unavailable. Resume a resumable operation with its original UUID and inputs; failed/conflict operations require an explicit new decision. See the [provider recovery contract](https://github.com/ZackaryW/saucepan/blob/v0.11.0/docs/managed-setup.md).

An existing raw manager requires explicit verified migration. Ordinary init and upgrade report its observed SHA256 and preserve it. `pspec init --force` authorizes the pinned official installer to migrate a supported default installation using that observed digest, with provider-verified backup and readiness reinspection. It does not migrate standalone overrides or update an already-ready manager. Download `install.ps1` or `install.sh` from the exact [v0.11.0 release](https://github.com/ZackaryW/saucepan/releases/tag/v0.11.0), verify against `SHA256SUMS` (or the pinned descriptor), and run externally:

```powershell
.\install.ps1 -Version v0.11.0 -Root "$HOME\.saucepan" -Operation UUID -MigrateUnmanaged -ExpectedSha256 SHA256
```

```sh
sh ./install.sh --version v0.11.0 --root "$HOME/.saucepan" --operation UUID --migrate-unmanaged --expected-sha256 SHA256
```

Replace UUID with a new UUID and SHA256 with the observed file digest after reviewing the selected file. Migration only supports initialized compatible stores; binary-only leftovers, unknown sidecars and unsupported roots require manual preservation or a separate root. No files are automatically relocated or deleted by Powerspec. Keep provider backups and receipts until recovery is confirmed.

Powerspec reserves an attempt record outside the store at `~/.powerspec/saucepan-setup/<root-hash>.json` before invoking migration. Keep it with the provider receipts. A repeated forced invocation cannot replay an uncertain or failed attempt; inspect/recover the recorded provider operation externally (using a setup-capable manager if the launcher is unavailable). Once the launcher is verified ready it is reused. Force does not bypass changed-file, link, sidecar, unsupported-store or busy-file checks. Migration may remain complete if later initialization fails.

With an explicit agent, forced initialization can repair a stale hook ownership receipt only when the uniquely identified native group already matches Powerspec's desired content. ZuAT rechecks equality during its receipt-only update, preserving native bytes and modification time. Edited or ambiguous hooks still fail; recovery operation identifiers are reported. Source-only initialization performs no hook work. Upgrade keeps its separate `--repair-hooks` option and its existing skill-only `--force` meaning.

Before migration, stop older Powerspec installations from using the default path: releases through 0.1.5 still contain the raw replacement lifecycle. Use an explicitly selected separate compatible executable for those consumers. This managed-setup adapter is the required consumer behavior; do not rely on an old consumer to protect the shared shim.

After provider recovery, rerun `pspec init` with the original options. `upgrade` requires the initial source selection and does not substitute for init.

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

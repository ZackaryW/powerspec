# Remote sources

Powerspec delegates Git acquisition and retained materialization to Saucepan. Profiles declare friendly aliases and exact Git recipes; Powerspec does not clone repositories or keep a separate user-level source registry.

## Managed Saucepan executable

Powerspec uses Zuu's managed-release lifecycle when a selected remote reference first needs the default Saucepan client. If the SDK's shared executable under `~/.saucepan/bin` is absent, Powerspec selects an official Saucepan 0.5 or 0.6 GitHub release for the current platform, validates `--version` and `--help` on a staged file, and publishes it atomically. These are the verified CLI protocol lines supported by the installed SDK boundary. An explicitly supplied SDK client bypasses this lifecycle.

Successful release checks are cached for 24 hours. A fresh matching check avoids GitHub discovery. When a later discovery or upgrade fails, Zuu retains a compatible installed executable; when no compatible executable can be produced, Powerspec reports the managed-tool failure before attempting the source operation. Constructing a catalog or running a bundled-only profile does not trigger installation: the lifecycle is lazy until a selected Git recipe needs materialization.

## Profile recipe and Saucepan application contract

The source identity in `@gitsource/<identity>/<selector>` is a profile-owned alias. The same effective profile graph declares its recipe:

```toml
skills = ["@gitsource/zmem/skills/*"]

[[source]]
id = "zmem"
provider = "git"
origin = "https://github.com/ZackaryW/zmem"
reference = "main"
```

Identical declarations can be shared across selected profiles. Different recipes for the same alias are a composition error. `builtin` remains reserved.

All recipes are materialized through one Saucepan application named `powerspec`. Powerspec creates the Saucepan store and registers that application lazily during `pspec init` or `pspec sync` when a selected recipe is missing. Repeating either command reuses a matching current materialization without refreshing it. Powerspec uses the application view, source history, and artifact path to locate exact recipe matches; one application may therefore contain many sources.

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
- `pspec init` and `pspec sync` may acquire a selected recipe only when it is missing;
- explicit upgrade is the only Powerspec operation that refreshes an existing selected recipe.

An unavailable Powerspec app during read-only lookup, ambiguous matching source, missing full-root artifact, failed acquisition, or invalid replacement produces a source-specific diagnostic. Such failure does not turn an earlier valid binding into a successful replacement.

## Reusable catalogs and direct skills

Reusable catalogs are discovered from `.pspec` directories inside the materialized repository. A repository may publish nested catalogs, whose resources share the registered source namespace. `openspec/.pspec` is always private consumer configuration and is excluded. Discovery validates all published declarations and rejects duplicate identities before a replacement binding becomes visible. A missing reusable catalog cancels that registration attempt.

Direct skill references do not require `.pspec`. Their selectors are source-relative:

- `@gitsource/tools/skills/example` selects that one skill root;
- `@gitsource/tools/skills/*` selects immediate child skill roots;
- `@gitsource/tools/skills/**` explicitly selects skill roots recursively.

Only directories containing `SKILL.md` participate. Selected declarations are validated together, ordered by source-relative path, and retain the complete skill directory. Absolute paths, parent traversal, canonical or symlink escapes, empty initial matches, and duplicate selected declared names are errors. The installed name comes from `SKILL.md`, not the source identity or folder name.

Conceptually, explicit reusable discovery follows this boundary:

```python
recipe = {"provider": "git", "origin": "https://example.test/team/tools", "reference": "main"}
binding = SaucepanSources().ensure("team-tools", recipe)
catalogs = ExternalCatalogs().register(binding)
catalog = Catalog(sources=catalogs.sources(), gitsources={"team-tools": binding})
```

The registration step only validates and exposes resources. It does not provision a skill.

## Upgrade success boundary

Run `pspec upgrade --agent <agent>` from inside the owning Git repository. Upgrade processes every remote skill selector in the consumer's effective profile bundle:

1. resolve the previously materialized selections without fetching;
2. refresh every referenced profile recipe through the Powerspec Saucepan app;
3. validate all replacement selectors and target collisions;
4. reconcile every selected bundled, local, and refreshed skill through ZuAT;
5. reconcile the generic hook dispatcher for the target agent;
6. identify obsolete copies only from the prior verified remote selection and current ZuAT ownership;
7. submit all obsolete copies in one recoverable ZuAT removal operation;
8. verify their absence before reporting success.

No removal begins until all refresh, validation, collision, skill provisioning, and hook reconciliation work succeeds. A failed or unknown source does not establish absence. An empty replacement is accepted only for a selector that previously resolved successfully.

If removal or final verification fails, Powerspec asks ZuAT to restore the removal operation's complete before-state. The command reports failure after successful restoration and reports a partial result if ZuAT cannot restore it. Source caches and already completed non-removal updates are outside this rollback boundary.

Saucepan's current public API does not expose source deregistration evidence. An unavailable Powerspec app or missing materialization therefore remains an error and preserves installed copies; Powerspec does not infer an intentional deletion from that error.

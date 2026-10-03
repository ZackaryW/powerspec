# Remote sources

Powerspec delegates Git acquisition and retained materialization to Saucepan. It does not clone repositories, infer repository URLs from profile references, or keep a second source-alias registry.

## Saucepan identity contract

The source identity in `@gitsource/<identity>/<selector>` is the name of an existing Saucepan app registration. That registration must have touched exactly one Git source. For example, `@gitsource/zmem/skills/*` resolves the registered Saucepan app named `zmem`; it does not imply `github.com/ZackaryW/zmem`.

The registered app must contain a current full-repository artifact. Powerspec uses Saucepan's app view, source history, and artifact path to locate that materialization. Read-only lookup never calls acquisition, repair, or installation.

Explicit acquisition or upgrade reuses the Git origin and reference recorded by Saucepan, requests the complete repository, and retains:

- the Saucepan app identity and canonical source ID;
- the recorded repository origin and requested Git reference;
- the resolved Git revision and artifact ID;
- the verified managed directory returned by Saucepan.

Saucepan performs a full repository acquisition before Powerspec applies a profile's path selector. A selector such as `skills/*` therefore controls which resources participate in composition and installation; it does not reduce Git network transfer.

## Lifecycle boundaries

Registration, selection, installation, synchronization, and upgrade are separate actions:

- Saucepan owns app registration and source acquisition.
- Powerspec validates the existing materialization and selects resources.
- ZuAT owns native agent installation and installation provenance.
- `pspec sync` reuses existing materializations and does not fetch, install, or remove skills.
- explicit upgrade is the only Powerspec operation that may refresh a registered source.

An unavailable app, ambiguous app with multiple touched Git sources, missing full-root artifact, failed refresh, or invalid replacement produces a source-specific diagnostic. Such failure does not turn an earlier valid binding into a successful replacement.

## Reusable catalogs and direct skills

Reusable catalogs are discovered from `.pspec` directories inside the materialized repository. A repository may publish nested catalogs, whose resources share the registered source namespace. `openspec/.pspec` is always private consumer configuration and is excluded. Discovery validates all published declarations and rejects duplicate identities before a replacement binding becomes visible. A missing reusable catalog cancels that registration attempt.

Direct skill references do not require `.pspec`. Their selectors are source-relative:

- `@gitsource/tools/skills/example` selects that one skill root;
- `@gitsource/tools/skills/*` selects immediate child skill roots;
- `@gitsource/tools/skills/**` explicitly selects skill roots recursively.

Only directories containing `SKILL.md` participate. Selected declarations are validated together, ordered by source-relative path, and retain the complete skill directory. Absolute paths, parent traversal, canonical or symlink escapes, empty initial matches, and duplicate selected declared names are errors. The installed name comes from `SKILL.md`, not the source identity or folder name.

Conceptually, explicit reusable registration follows this boundary:

```python
binding = SaucepanSources().acquire("team-tools")
catalogs = ExternalCatalogs().register(binding)
catalog = Catalog(sources=catalogs.sources(), gitsources={"team-tools": binding})
```

The registration step only validates and exposes resources. It does not provision a skill.

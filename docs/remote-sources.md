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

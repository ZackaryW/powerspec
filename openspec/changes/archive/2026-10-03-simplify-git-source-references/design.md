# Design

## Context

See proposal.md for motivation. Profiles currently validate every skill entry with the same qualified-reference parser, while direct Git skills use a special `@gitsource/<alias>/...` branch in catalog selection, deferred composition, arming, and upgrade reconciliation. The effective profile graph already merges `[[source]]` recipes before resolving skills, so the namespace marker carries no additional acquisition information.

## Goals / Non-Goals

**Goals:**

- Give direct Git skill selectors one concise canonical form: `<source-alias>/<source-relative-path-or-pattern>`.
- Keep source recipes authoritative for repository origin and revision.
- Preserve source-relative containment, deterministic wildcard expansion, provenance, installation names, and upgrade behavior.
- Use the same canonical identity in composed selections, status, arming, provisioning diagnostics, and upgrade bookkeeping.

**Non-Goals:**

- Inferring repositories from aliases, GitHub organizations, or folder names.
- Changing Saucepan acquisition or ZuAT installation contracts.
- Adding shorthand for profiles, contexts, traits, or catalog-qualified skills.
- Creating a generic path utility; this is resource-identity policy owned by the catalog/profile layer.

## Decisions

### Treat a non-`@` skill entry as a declared Git-source selector

The skills field supplies the resource kind, so a value such as `zmem/skills/*` can reserve its first segment for a source alias. Qualified `@builtin/name` and `@source/name` references retain their current catalog meaning. A bare selector whose alias is not declared remains structurally valid during profile loading but fails composition with the existing missing-source diagnostic, because declarations are known only after the effective graph is assembled.

Alternative: keep `@gitsource` as an explicit namespace. This repeats information already carried by `[[source]]` and is the syntax being removed. Alternative: put selectors inside each source table. That couples source acquisition recipes to one profile's selection and prevents the same declared recipe from supporting different selectors in composed profiles.

### Make the shorthand the canonical direct-Git identity

The parser will validate qualified catalog references and source-relative selectors through separate paths. Selected direct Git resources will retain canonical identities such as `zmem/skills/zmem-query-memory`, rather than translating back to the removed `@gitsource` spelling. Composition, `armed`, status, provisioning, and upgrade detection will use shared parsing helpers so the authored and observable identities agree.

Alternative: normalize to the old string internally. That reduces the first patch but leaks the redundant syntax through status, diagnostics, and conditions, leaving two identities for one resource.

### Reject the old spelling

Profile validation will reject `@gitsource/...` with a migration-oriented diagnostic. Supporting both indefinitely would make malformed or stale configuration harder to identify and would preserve branches throughout the code. This is an intentional breaking authoring migration while installed skill names and remote materializations remain compatible.

## Risks / Trade-offs

- **Existing profiles stop loading** → Update all bundled profiles and document the mechanical replacement from `@gitsource/<alias>/...` to `<alias>/...`; return an explicit legacy-syntax diagnostic.
- **Bare strings could be mistaken for ordinary skills** → Only `skills` accepts the form, the first segment must be a valid source alias, and undeclared aliases fail without URL inference.
- **Remote detection may diverge across workflows** → Centralize parsing/classification helpers and exercise composition, deferred status, arming, provisioning, sync, and upgrade tests.

## Migration Plan

1. Add and test the canonical skill-reference parser and direct-Git classifier.
2. Update composition, catalog selection, status/arming identities, and upgrade reconciliation to use it.
3. Migrate bundled profiles and public documentation.
4. Run focused remote-source/profile tests, strict OpenSpec validation, then the full suite.

Rollback requires reverting both parser behavior and bundled profile strings; existing Saucepan materializations and ZuAT installations need no data migration.

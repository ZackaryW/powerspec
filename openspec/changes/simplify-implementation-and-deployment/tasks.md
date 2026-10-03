# Tasks

## 1. Manifest Version 2

- [ ] 1.1 Replace the version 1 manifest models with version 2's single optional prompt and `after`/`replace` positions, add explicit diagnostics for removed fields and versions, and verify focused manifest-validation tests pass.
- [ ] 1.2 Simplify dynamic composition and input resolution by removing hints, before-placement, and combine accumulation while preserving after ordering, replacement precedence, ancestry suppression, containment, and exact ATX section errors; verify the focused skill input and document suites pass.
- [ ] 1.3 Migrate every bundled `pspec.toml`, skill explanation, and resolution example to version 2 and verify bundled TDD and decision-skill resolutions match their reviewed outputs.

## 2. Shared Infrastructure Reuse

- [ ] 2.1 Route validated temporary-state publication through `utils.atomic.replace_bytes`, remove the duplicate publisher, and verify unchanged, successful, and failed-publication state tests pass.
- [ ] 2.2 Parse skill frontmatter through ruamel.yaml's safe loader, remove Powerspec's direct PyYAML use and declaration, and verify valid and malformed catalog fixtures retain their diagnostics.
- [ ] 2.3 Consolidate overlapping version parsing and executable inspection used by initialization, doctor, and Saucepan checks without moving their application policies into utilities; verify their focused command and failure-category tests pass.

## 3. Versioned Package Distribution

- [ ] 3.1 Make compatible Saucepan SDK, ZuAT, and Zuu versions available from the target package index and verify a clean resolver can obtain each declared artifact without Git.
- [ ] 3.2 Replace Powerspec's Git URL requirements with reviewed compatibility ranges, update the committed uv lock, and verify `uv lock --check` plus the affected Saucepan and ZuAT integration tests pass.
- [ ] 3.3 Add release verification that builds with source overrides disabled, rejects VCS or local-path runtime metadata, and installs the wheel in a clean environment where command help and packaged-resource discovery succeed; document and run the release procedure.

## 4. Canonical CLI Surface

- [ ] 4.1 Migrate repository documentation, managed hook payloads, and tests to grouped `resolve` and `state` commands, then remove the hidden `skill`, `hook`, and `flush` aliases and verify CLI help, syntax, stdout/stderr, and exit-code tests pass.

## 5. Integrated Verification

- [ ] 5.1 Run `uv run pytest`, validate the OpenSpec change strictly, and compare the built dependency tree and source line count with the audit baseline; record any retained dependency or code whose removal claim was not achieved.

# Tasks

## 1. Canonical Source-Relative Skill References

- [x] 1.1 Add strict skill-reference parsing that accepts qualified catalog identities or `<source-alias>/<path-pattern>`, rejects legacy `@gitsource` and malformed selectors, and verify focused catalog/model tests cover exact, wildcard, recursive, unknown-alias, traversal, and legacy cases.
- [x] 1.2 Make direct Git selection return source-relative canonical identities with unchanged provenance and complete resource roots, and verify catalog tests cover deterministic expansion, declared names, duplicate names, containment, and empty selections.

## 2. Lifecycle Integration and Authored Resources

- [x] 2.1 Use the shared reference classification in profile composition, deferred status, `armed`, installation, sync, and upgrade reconciliation; verify focused profile, condition, status, installation, sync, source-integration, and upgrade tests expose only source-relative identities.
- [x] 2.2 Migrate bundled zmem and ADHD profiles plus public source/foundation documentation to `<source-alias>/<path-pattern>`, and verify packaged resource validation and documentation examples contain no active `@gitsource` syntax.

## 3. Integrated Verification

- [x] 3.1 Validate the OpenSpec change strictly and run the complete `uv run pytest` suite, recording any intentionally retained historical `@gitsource` text only inside archived changes or the migration contract.

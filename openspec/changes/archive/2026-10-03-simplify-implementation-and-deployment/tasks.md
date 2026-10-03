# Tasks

## 1. Manifest Version 2

- [x] 1.1 Replace the version 1 manifest models with version 2's single optional prompt and `after`/`replace` positions, add explicit diagnostics for removed fields and versions, and verify focused manifest-validation tests pass.
- [x] 1.2 Simplify dynamic composition and input resolution by removing hints, before-placement, and combine accumulation while preserving after ordering, replacement precedence, ancestry suppression, containment, and exact ATX section errors; verify the focused skill input and document suites pass.
- [x] 1.3 Migrate every bundled `pspec.toml`, skill explanation, and resolution example to version 2 and verify bundled TDD and decision-skill resolutions match their reviewed outputs.

## 2. Shared Infrastructure Reuse

- [x] 2.1 Route validated temporary-state publication through `utils.atomic.replace_bytes`, remove the duplicate publisher, and verify unchanged, successful, and failed-publication state tests pass.
- [x] 2.2 Parse skill frontmatter through ruamel.yaml's safe loader, remove Powerspec's direct PyYAML use and declaration, and verify valid and malformed catalog fixtures retain their diagnostics.
- [x] 2.3 Consolidate overlapping version parsing and executable inspection used by initialization, doctor, and Saucepan checks without moving their application policies into utilities; verify their focused command and failure-category tests pass.

## 3. Pinned Build Resources

- [x] 3.1 Replace the tracked upstream OpenSpec skill directories with a pinned custom-Hatch-hook source declaration; materialize only complete selected skills plus license/provenance into contained staging, and verify missing revisions, invalid roots, mismatches, and path escapes fail the build.
- [x] 3.2 Include the validated OpenSpec snapshot and digest manifest in the sdist, rebuild its wheel offline, and verify it matches the direct wheel's builtin resource paths and bytes without runtime source acquisition.

## 4. Canonical CLI Surface

- [x] 4.1 Migrate repository documentation, managed hook payloads, and tests to grouped `resolve` and `state` commands, then remove the hidden `skill`, `hook`, and `flush` aliases and verify CLI help, syntax, stdout/stderr, and exit-code tests pass.

## 5. Integrated Verification

- [x] 5.1 Run `uv run pytest`, validate the OpenSpec change strictly, and compare the built dependency tree and source line count with the audit baseline; record any retained dependency or code whose removal claim was not achieved.

Verification evidence: `389 passed, 2 skipped`; strict OpenSpec validation
passes; Python source changed from 5,158 to 5,144 lines (-14). Powerspec's
direct runtime requirements fell from eight to seven by removing PyYAML, while
PyYAML remains transitively required by ZuAT as expected. The full lock grew
from 28 to 31 packages because Hatchling and its build-test dependencies are
now explicit development requirements.

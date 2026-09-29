## 1. Development setup

- [x] 1.1 Add Typer and development pytest dependencies with uv, retain uv_build, add generated-file ignore rules, and verify dependency imports and the lockfile.

## 2. CLI scaffold

- [x] 2.1 Add focused behavioral tests for help, parsing, placeholder outcomes, silent imports, and unchanged fixture state; observe expected failures against the greeting before implementing the command surface.
- [x] 2.2 Implement the Typer app and individual command modules under src/powerspec/cli/, wire pspec/powerspec to the same entrypoint with powerspec.main delegation, and document command usage and placeholder status in README. Verify the focused tests pass with uv run pytest.

## 3. Integration and handoff

- [x] 3.1 Verify both real console entrypoints from an isolated working directory, run the complete scaffold test suite and strict OpenSpec validation, and update the skill-bootstrap plan to depend on this scaffold without marking its domain implementation tasks complete.

Validation (2026-09-29): the initial entrypoint test failed because it returned the greeting instead of help. After implementation, `uv run pytest -q` passed all 31 tests, including real console-script subprocesses outside the checkout, placeholder diagnostics, syntax validation, and unchanged fixture state. `uv lock --check` and strict validation of this change and establish-skill-bootstrap-resolution passed. No real agent settings were modified. The larger change's domain tasks remain open.

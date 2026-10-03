# Tasks

Prerequisites: establish-profile-consumer-resolution and implement-skill-content-resolution. Reuse their composition, inspection, and incremental CLI contracts. Hook registration is a later change.

## 1. Packaged resource preparation

- [x] 1.1 Select and vendor compatible committed upstream OpenSpec skill directories with complete resources, upstream license, and repository/commit/path provenance; verify the snapshot against the pinned upstream revision and target OpenSpec CLI.
- [x] 1.2 Switch uv_build to Hatchling and include builtin profiles, authored contexts/traits/skills, and the pinned upstream snapshot in wheel/sdist; verify resource enumeration includes manifests, inactive branches, and attribution while retaining uv and uv run pytest.
- [x] 1.3 Add installed-package resource access; build/install outside the checkout and rebuild a wheel offline from sdist with dependencies available, verifying equivalent selected resources without source/cache paths, upstream fetches, or generation.
- [x] 1.4 Document maintainer snapshot refresh versus normal local builds/installations; verify missing packaged resources yield diagnostics rather than a remote/generation fallback.

## 2. Scoped ZuAT provisioning

- [x] 2.1 Extend the explicit-agent adapter with installation planning from profile target descriptors; verify one profile scope, explicit project_root for project scope, cross-profile scope preservation, reserved identities, and target/provenance reporting.
- [x] 2.2 Implement inspected provisioning with matching reuse and conflict detection; verify unmanaged/modified targets, unsupported scopes, missing project roots, partial completed/failed results, no all-agent default, and no silent scope switch using disposable homes.
- [x] 2.3 Provision complete bundled OpenSpec/bootstrap/TDD resources; verify inactive branches survive, ordinary OpenSpec lookup returns null, the Python bundle omits BDD, and installation uses no upstream download or saucepan cache.
- [x] 2.4 Document profile scope and selection versus native availability; verify excluding a profile neither removes shared installations nor claims native enable/disable control.

## 3. Repository initialization

- [x] 3.1 Implement Git-root OpenSpec/Powerspec setup in init.py with OpenSpec local skill generation disabled; verify fresh/nested/worktree invocations, persistent configuration preservation, existing source/native skill preservation, and no generated local skills for user-only bundles.
- [x] 3.2 Establish a current.toml ignore rule while leaving config.toml trackable; verify existing ignore rules and variable files remain intact, and tracked current files are not falsely reported as untracked.
- [x] 3.3 Connect explicit-agent scoped provisioning to init and update help/readiness checks; verify a user-scoped global profile plus project-scoped selected bundle lands each at its own target, unresolved agent is diagnosed, and repeated init preserves existing values.
- [x] 3.4 Document initialization, conflicts, and partial-failure recovery; run examples in disposable repositories and confirm installation reports availability without claiming hook delivery, testing execution, or config.yaml synchronization.

## 4. Distribution integration milestone

- [x] 4.1 Initialize two isolated consumers from an installed distribution and resolve different branches from one complete shared installation; verify no branch-driven reinstall and no shared-skill deletion after an exclusion.
- [x] 4.2 Run relevant packaging/adapter/init/CLI tests with uv run pytest and openspec validate bundle-resources-and-initialize --strict; record wheel/sdist/offline evidence and confirm tests wrote no real agent home.

## Verification evidence

- `uv run pytest -q`: 192 tests passed, including mixed installation scopes, unmanaged/edited preservation, repeat init, global-only selection, worktrees, variable preservation, and tracked current-file reporting.
- `openspec validate --all --strict`: 8 items passed.
- Built wheel/sdist with Hatchling, installed the wheel with pinned dependencies offline in an isolated Python 3.12 environment outside the checkout, and initialized two temporary Git consumers with one disposable Codex home and ZuAT registry.
- The consumers resolved autonomous and exhaustive branches of one shared pspec-smarter-decision installation. The second init reused all installed skills; skill bytes and modification times stayed unchanged. Excluding the profile preserved its shared installation. The installed ordinary OpenSpec skill returned literal null.
- Offline wheel rebuild from the sdist matched every archive entry's bytes, excluding RECORD. No verification used the real agent home or registry.

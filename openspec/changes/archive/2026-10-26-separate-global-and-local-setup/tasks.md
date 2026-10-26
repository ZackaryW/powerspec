# Tasks

## 1. Source publication safety net

- [x] 1.1 Add `SaucepanSources` support for publishing only candidates whose key has no prior `selected` entry, reusing the pending-key equality check; verify with a `tests/test_sources.py` case where a first-time key is published and a replacement key stays pending
- [x] 1.2 In `install_consumer`, publish first-time candidates before skill provisioning and keep commit/reject for replacements; verify with a `tests/test_installation.py` case where a skill conflict still leaves the first-time selection readable by `lookup()`, and one where a failed replacement keeps the prior selection
- [x] 1.3 Add a regression test that reproduces the reported loop (init --agent with a conflicting skill, then upgrade) and verify upgrade no longer reports "no selected materialization"

## 2. Conflict replacement in init

- [x] 2.1 Report completely inspected unowned/conflict outcomes as replaceable in `provision_skills` results, and append the `pspec init --agent <agent> --force` remedy to their diagnostics; verify with `tests/test_provisioning.py` cases, including that incomplete or unsupported inspection is not marked replaceable
- [x] 2.2 Pass `force` from `init --agent --force` into skill provisioning; verify with a `tests/test_init_force.py` case where a differing unowned skill is replaced and its operation id is reported
- [x] 2.3 Add the interactive path to init: when stdin and stderr are both TTYs and `--force` is absent, list the replaceable skills once, confirm (default no) on stderr, then run a forced pass for only those plans; verify with CLI tests that cover accept, decline and a non-TTY run (no prompt, remedy printed)
- [x] 2.4 Ensure the final init error names the --force remedy once when replaceable conflicts remain; verify the output in the decline and non-TTY tests

## 3. Optional scope

- [x] 3.1 Add `--scope local|global|all` (default `all`) to init: `local` rejects `--agent` and skips agent assets; `global` requires `--agent`, uses lookup-only sources and leaves consumer files unchanged; verify with `tests/test_bootstrap_lifecycle.py` CLI cases for each scope, including global with a missing selection failing with the local-init hint
- [x] 3.2 Update init `--force` and `--scope` help text to match the spec; verify with a help-output test

## 4. Documentation and verification

- [x] 4.1 Update `docs/initialization.md`, `docs/skill-installation.md` and `docs/remote-sources.md` for the single-command conflict flow, the new `--force` meaning, `--scope` and the first-time publication rule; verify that no doc still says init --force leaves skills untouched
- [x] 4.2 Run `uv run pytest` and `openspec validate separate-global-and-local-setup --strict`, and verify both pass

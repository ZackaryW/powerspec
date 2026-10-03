# Tasks

## 1. Temporal-state service

- [x] 1.1 Add the TOML round-trip dependency and implement nearest-consumer full reset with strict input/candidate validation and atomic replacement; verify missing, already-empty, populated, malformed, worktree, and injected publication-failure cases preserve the required bytes.
- [x] 1.2 Implement direct change-scoped removal while preserving shared values, other changes, comments, and formatting; verify existing, absent, quoted/dotted change names, empty-name rejection, and empty `_change` cleanup.

## 2. CLI and lifecycle contract

- [x] 2.1 Replace the flush placeholder for both aliases with updated/unchanged output and nonzero diagnostics; verify nested ownership, no-consumer behavior, `--change`, help/syntax, and mutation boundaries through CLI tests.
- [x] 2.2 Document full versus change-scoped cleanup and the post-success archive handoff; update readiness text and verify examples leave persistent configuration and `config.yaml` unchanged.

## 3. Integration checkpoint

- [x] 3.1 Run the complete test suite, build distributions, validate packaged dependency metadata, and run `openspec validate implement-temporary-state-flush --strict` plus a disposable installed-command walkthrough.

## Verification evidence

- `uv run pytest -q`: 252 passed and one existing opt-in acceptance test skipped.
- Hatchling built the wheel and sdist; the wheel contains the archive context and declares `tomlkit<1,>=0.13`.
- A disposable virtual environment installed the wheel and all declared dependencies. Both `pspec flush --change finished` and `powerspec flush` updated the intended file while tracked persistent state remained unchanged.
- Focused fixtures cover missing/already-empty/full state, direct quoted change keys, comment and sibling preservation, malformed state, worktrees, no consumer, both aliases, and injected replacement failure with staging cleanup.
- `pspec sync` published the managed archive handoff in this consumer's `config.yaml`. It separately diagnosed the currently unavailable external `i-have-adhd` Saucepan source after local reconciliation.
- Strict OpenSpec validation passed.

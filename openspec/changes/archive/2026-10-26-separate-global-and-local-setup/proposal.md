# Proposal

## Why

`pspec init --agent <agent>` cannot finish when selected user-scope skills already exist as unowned or locally modified copies, for example skills written earlier by another installer. `init --force` does not authorize replacing skills. The documented recovery, `pspec upgrade --agent <agent> --force`, needs committed source selections, which init discards when provisioning fails. A first-time user ends up in a loop with no single command that completes setup. Setup should take one command, and that command should resolve the conflicts it finds, with consent.

## What Changes

- `pspec init --agent <agent>` resolves skill conflicts in the same run. After non-conflicting skills are provisioned, init lists every completely inspected unowned or conflicting target and asks once whether to replace them. ZuAT keeps a recoverable backup of each one.
- When stdin is not an interactive terminal, init does not prompt. It fails and names `pspec init --agent <agent> --force` as the one-line remedy.
- **BREAKING**: `init --force` with `--agent` also authorizes recoverable replacement of completely inspected unowned or locally modified selected skills, the same authority `upgrade --force` already has. It still does not bypass incomplete inspection, unsupported targets, source validation, hook ownership checks or obsolete-skill removal safeguards.
- Safety net: source candidates with no prior selection are committed once source validation succeeds, before agent provisioning. A declined prompt or a later failure therefore never leaves a consumer without the selections that `upgrade` and `sync` need. Replacements of existing selections keep the full-success commit boundary.
- Failures for unowned or conflicting skills name the remedy command.
- Optional: `pspec init --scope local|global|all` (default `all`) lets advanced users run only the per-repository half (consumer and sources) or only the per-machine half (skills and hooks). It is not required for normal setup.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `cli-product-surface`: init prompts to replace conflicting skills in a terminal; `init --force` adds skill replacement authority; init gains the optional `--scope`.
- `user-skill-installation`: init, not only upgrade, may perform forced recoverable replacement; conflict diagnostics name the remedy.
- `remote-sources`: first-time selections are published after source validation, separately from agent provisioning.

## Impact

- Code: `src/powerspec/cli/init.py` (prompt, terminal detection, `--scope`, force wiring), `src/powerspec/installation.py` (early commit of first-time keys, second forced pass), `src/powerspec/sources.py` (commit a subset of candidates), `src/powerspec/provisioning.py` (conflict reporting, remedy diagnostics).
- Docs: `docs/initialization.md`, `docs/skill-installation.md`, `docs/remote-sources.md`.
- Tests: init in a terminal accepts and declines, non-interactive init fails with the remedy, `init --force` replaces skills, and a regression test for the original init/upgrade deadlock.
- Behavior: scripts that run `init --force --agent X` expecting skills to stay untouched will now replace differing copies (with backups).

# Design

## Context

`install_consumer` opens a workspace, which stages source candidates as `pending`. It then runs `provision_skills` and `provision_hooks`, and calls `SaucepanSources.commit()` only if both succeed. Otherwise it calls `reject()`, which deletes the pending entries. `lookup()`, used by `upgrade` and `sync`, reads only `selected` entries.

`provision_skills` already has a forced path: when `force` is set and inspection is `complete` with classification `unowned` or `conflict`, it calls ZuAT `install(force=True)`, which archives the old copy and replaces it. Only `upgrade` passes `force` today.

The CLI has no interactive prompts yet. Progress goes to stderr and results go to stdout.

## Goals / Non-Goals

**Goals:**
- `pspec init --agent X` completes setup in one invocation when foreign or edited skill copies exist, with the user's consent.
- No failure path leaves a first-time consumer without the selections it needs to recover.

**Non-Goals:**
- Replacing targets with incomplete inspection, unsupported targets, or hook conflicts. These keep their current failures.
- Coordinating with other installers that rewrite the same native paths.
- Changing `upgrade`'s obsolete-removal rules.

## Decisions

### D1: Provision in two passes; resolve conflicts between them

1. **Pass 1:** run `provision_skills(plans, force=force)` as today. Outcomes classified as complete `unowned` or `conflict` are marked replaceable instead of plain failures.
2. **Decide:**
   - `--force` given: replace without asking.
   - Interactive (`sys.stdin.isatty()` and `sys.stderr.isatty()`): print the replaceable skill names to stderr, note that originals are backed up, and ask once with `typer.confirm(..., default=False, err=True)`.
   - Otherwise: do not prompt. Fail with the remedy `pspec init --agent X --force`.
3. **Pass 2:** on consent, call `provision_skills(replaceable_plans, force=True)`. This reuses the existing forced branch, and ZuAT rechecks state inside its own locked preflight.

Rationale: one prompt for the whole batch, asked after the noisy progress output. Pass 2 reuses a code path that already exists and is tested, so no new ownership logic is needed. Asking per skill would mean 12 prompts in the reported case.

Alternatives:
- *Prompt inside `provision_skills` for each skill.* This mixes I/O into a non-CLI module and asks many times.
- *Inspect everything up front, then act.* That is an extra full inspection pass, and pass 1 already provides the information.

### D2: `init --force` adds skill replacement authority

`--force` on `init` now also passes `force=True` to skill provisioning. This brings init in line with `upgrade --force`, and gives non-interactive users (CI, agents running the CLI) a one-command path. The excluded cases are unchanged (incomplete inspection, unsupported targets, hooks, obsolete removal).

Alternative: a separate `--replace-skills` flag. It is more precise, but adds another flag to learn, and the user explicitly chose to fold this into `--force`.

### D3: Commit first-time selections after validation (safety net)

Candidates with **no prior `selected` entry** are committed after source validation and before provisioning. Candidates that **replace** an existing selection keep today's boundary: committed only if provisioning fully succeeds, rejected otherwise. This requires `SaucepanSources` to commit a subset of keys while reusing `_commit_locked`'s pending-key equality check.

Rationale: if the prompt is declined or provisioning fails, `upgrade` and `sync` still work and a rerun of `init` reuses the selection. Replacements keep the strict boundary because the prior selection is the baseline that `upgrade` uses to compute obsolete removals. Moving that baseline when provisioning fails could hide obsolete skills from the older revision.

### D4: Remedy in diagnostics

In `provision_skills`, the `unowned`/`conflict` fallback diagnostic adds the remedy command. Init's final error states it once when replaceable failures remain (declined, or non-interactive).

### D5: Optional `--scope local|global|all`

The default `all` is the single-command path above. `local` establishes the consumer and prepares and commits sources, with no agent-asset writes and no `--agent`. `global` requires `--agent`, reads existing selections only, and runs D1/D2 for skills and hooks. This is a power-user split, not part of onboarding. Init without `--agent` already behaves as `local`.

## Risks / Trade-offs

- [`--force` now overwrites hand-edited skills in scripts that used to be safe] → Replacement is recoverable through ZuAT backups and operation IDs. Init prints each operation ID. Docs and release notes flag the breaking change.
- [The terminal check gives a false positive under some agent harnesses or a false negative under `script`/tmux] → Require both stdin and stderr to be TTYs, and default the prompt to No. A wrong guess either asks a question the user can decline, or falls back to the non-interactive remedy.
- [Another installer, such as the OpenSpec CLI, rewrites replaced skills again later] → Out of scope. The docs name it as a known co-writer, and the prompt makes repeated conflicts visible.
- [The second pass races a concurrent writer] → ZuAT's locked preflight rechecks state, and a changed target fails as it does today.

## Migration Plan

No data migration. A consumer that is already stuck recovers with a single `pspec init --agent X` (accept the prompt) or `pspec init --agent X --force`. Rollback: revert the release. Selections committed early stay valid under the old code.

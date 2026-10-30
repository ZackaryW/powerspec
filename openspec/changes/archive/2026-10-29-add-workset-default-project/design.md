# Design

## Context

OpenSpec owns workset definitions (`name`, ordered `members` of `name`/`path`, optional `tool`) and Powerspec reaches them only through the CLI boundary in `workset_openspec.OpenSpec`. Powerspec never edits OpenSpec's registry; appending is remove-then-recreate through the CLI. User-level Powerspec data already lives under `~/.powerspec/` (`config.toml`, `saucepan-setup/`), and `utils/atomic.replace_bytes` provides atomic file replacement. `openspec workset list --json` took 513-555 ms per call on this machine.

The hook side builds on `support-antigravity-hooks`: multi-project payloads produce an instruction line plus labeled sections composed by `compose_sections`. See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**
- A user can declare, see, and clear one default member per workset.
- Multi-project Antigravity sessions on a workset with a default name it as the fallback with no extra process calls.
- Defaults survive launch and append without manual re-entry.

**Non-Goals:**
- Changing OpenSpec's workset model or registry, or proposing an upstream field.
- Using the default to choose a project automatically (the agent still decides; the default is only the fallback).
- Codex and Claude sessions, which resolve one project from their working directory.
- Choosing where `openspec new change` writes; OpenSpec's own store defaults are unchanged.

## Decisions

### D1. Powerspec-owned file, keyed by workset name, with a member snapshot
`~/.powerspec/worksets.toml`:

```toml
[worksets.poc-ab]
default = "poc-ab-central"
path = "F:/(WORK) git poc/poc-ab-central"
members = ["F:/(WORK) git poc/poc-ab-admin-portal", "..."]
```

The name is the key the user types; `path` and `members` let the hook match without OpenSpec. The snapshot is what makes staleness detectable: if OpenSpec membership changes behind Powerspec's back, the snapshot no longer equals it and the default goes inert rather than pointing at the wrong place. Alternatives: an OpenSpec field (does not exist, and Powerspec must not edit the registry); first-member-by-order (rejected by the user: it cannot be set without recreating the workset); per-repository marker files (writes into repositories and cannot express "default for this workset" when a repository is in several worksets).

### D2. Hook matching is exact path-set equality, local only
The hook normalizes paths (resolve, `os.path.normcase`, forward slashes) on both sides and selects the entry whose `members` set equals the payload's `workspacePaths` set. Zero or several matches mean no default (several also writes a stderr note). It never calls OpenSpec: one call costs about 0.5 s, against a 5 s handler limit already shared with the payload read and per-project resolution. Subset or superset matches are rejected because they would name a default for a session that is not that workset.

### D3. Instruction wording and marking
With a match, the instruction becomes: follow only the section for the project you are actively implementing or updating changes in; if you cannot determine which project applies, use the default project `<label>` (`<path>`). The default's section heading gets a `(default)` marker. If the default contributes no guidance, it is still named and no empty section is emitted. The wording and the `(default)` marker live in Powerspec application code as part of each caller-supplied section label, so `compose_sections` needed no change.

### D4. Lifecycle hooks in existing commands
- `launch`: after the output workset is published, if the source default is current (snapshot equals OpenSpec's source membership), record the same label for the output, with the launched worktree path and the output members. Reuse an identical entry; keep and report a different existing one.
- `add`: after a verified append, refresh `members` of a current default; leave it untouched on failure. Non-current defaults are not refreshed, so staleness stays visible.

### D5. Show reports staleness with a reason
Show calls OpenSpec (an interactive command, where 0.5 s is fine) and reports one of: `current`, `stale: workset removed`, `stale: label no longer a member`, `stale: members changed`. Set and clear also validate through OpenSpec; nothing re-points automatically.

## Risks / Trade-offs

- **The snapshot goes stale when someone uses `openspec workset` directly** → inert, reported by show with a fix-it hint; no wrong default is ever named.
- **Path normalization differences** (drive-letter case, separators, the Antigravity payload's forward slashes versus OpenSpec's backslashes, seen in the spike) → one normalization function used by both writer and matcher, tested with both forms and with spaces and parentheses.
- **The agent may ignore the fallback** → delivery is not adherence, and docs say so.
- **Ordering dependency on `support-antigravity-hooks`** → the hook task group is gated on that change.

## End-to-end observation (2026-10-30)

With the dev Powerspec and local Zuat, a stored default for a two-member workset and the real `~/.gemini/config/hooks.json` dispatcher (both removed afterwards), a real `agy -p --add-dir` session over those two consumers reported the first paragraph ending "If you cannot determine which project applies, use the default project app-x-test (<path>)." and the `(default)` marker on that project's section. The instruction uses the OpenSpec member label while headings use the project directory name; they coincide for members added with `pspec workset add`, and the path disambiguates otherwise. Delivery does not establish that the agent follows the fallback.

## Migration Plan

Additive. No file exists until the first `set`. Rollback is reverting the change; the stray file is harmless and can be deleted.

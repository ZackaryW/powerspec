# Design

## Context

`pspec resolve hook sessionStart --agent antigravity --stdin-workspace` reads `workspacePaths` from the payload. For several paths it currently resolves every consumer's guidance and composes one message: an instruction paragraph, then `### <name> (<path>)` sections, the matching workset default marked `(default)`. Antigravity fires SessionStart once per conversation, before the agent knows which project it will touch, so the hook cannot itself choose the active project. Running the same command without `--stdin-workspace` from a project folder already returns exactly that project's guidance from its working directory.

## Goals / Non-Goals

**Goals:**
- Never deliver more than one project's guidance in a session-start message.
- Keep a deterministic project when a workset default matches; otherwise let the agent fetch the one it needs.

**Non-Goals:**
- Guessing the active project from `lastUserInput` or other payload fields.
- A new CLI command for on-demand guidance; the existing hook command serves it.
- Codex and Claude, which already resolve one project from their working directory.

## Decisions

### D1. Count distinct consumers, then branch
Resolve each existing listed path to its consumer once. Zero consumers: no output. One: deliver its guidance unlabeled, as a single-project session (two paths inside one repository, or one Powerspec repository beside plain folders, are one project). Two or more: build the project-list message. Alternative rejected: branching on the number of listed paths, which mislabels a session with one consumer and plain folders.

### D2. The message without a default
Intro, project list, command, no guidance body:

```
This session includes several Powerspec projects. Guidance is delivered for one project at a time: follow only guidance for the project you are actively implementing or updating changes in. To get a project's guidance, run `pspec resolve hook sessionStart --agent antigravity` from that project's folder.

Projects:
- api (F:/repos/api)
- web (F:/repos/web)
```

The command prints the Antigravity envelope; the agent reads the `systemMessage` text. Reusing it avoids a second public surface whose output could drift from what hooks deliver.

### D3. The message with a matching default
Same intro, plus "The default project is `<label>` (`<path>`); its guidance, if any, follows. Use it when you cannot determine which project applies." The default's list entry ends with `(default)`, and only its guidance follows under `### <name> (<path>)`, composed through the existing `compose_sections` helper with a single section; when that yields nothing (no default guidance) the intro and list stand alone. Non-default consumers' guidance is never resolved, which also removes their per-project catalog cost from the 5-second handler budget.

### D4. Failures
Discovery failure: stderr naming the path, omitted from the list; all found consumers failing exits 1 (unchanged contract). Default guidance failure: stderr, message without the guidance body, exit 0, since the list and command are still useful.

## Risks / Trade-offs

- **The agent may not run the command before working in a non-default project** → the instruction says to; delivery is not adherence, and the docs say so.
- **The default label may differ from the directory name in the list** → the path is shown beside both.
- **Breaking for anyone relying on combined sections** → only this week's unreleased behavior; no migration beyond setting a default.

## End-to-end observation (2026-10-30)

With the dev Powerspec, the real `~/.gemini/config/hooks.json` dispatcher and two consumers whose sessionStart bodies carry distinct tokens (files removed afterwards), a real `agy -p --add-dir` session over both reported: without a default, the intro and the two-entry project list and neither token; with `app-x-test` stored as the default, the same list with that entry marked `(default)` and only its token under its heading. Delivery does not establish that the agent runs the per-project command when it switches projects.

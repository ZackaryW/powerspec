---
name: pspec-skill-bootstrap
description: Resolve an intended skill through Powerspec using its owning OpenSpec consumer configuration. Use before other skills in a Powerspec-enabled workflow to receive applicable content or normal unsupported-skill fallback.
---

# Resolve a skill before using it

Follow this bootstrap directly; do not resolve `pspec-skill-bootstrap` through itself. Resolve only the skill selected for the current task, not every installed skill. Availability does not activate a workflow.

## Look up the intended skill

From the current task's working directory, run:

```text
pspec resolve skill <name> --agent <current-agent>
```

When the calling workflow has an active OpenSpec change, append `--change <name>` and retain it on reruns. Otherwise omit it; do not infer an active change from available variable tables.

When the host identifies the installed copy it selected, append `--selected "<installed-directory-or-SKILL.md>"` and retain it on reruns. Powerspec validates that path against the invoking agent's installed candidates. Do not substitute an authoring-source path or choose user/project precedence yourself. If selection is ambiguous, obtain the host's selected path before retrying.

Use the intended installed skill's name and the actual invoking agent's identifier. Establish an unknown agent identity from the host context or ask; do not infer it from the shell or search all agents. Keep the task's working directory so lookup uses its owning project configuration rather than the installed skill's directory.

Output is plain Markdown by default. Use `--json` when a structured result is needed; it represents the same lookup outcome.

Perform lookup before loading the skill's full procedure. The command retrieves guidance; it does not execute or install the skill.

## Follow the result

| Result | Action |
| --- | --- |
| Successful literal `null` (also with `--json`) | The selected installed copy has no `pspec.toml`. Read that copy's normal entrypoint and follow it within the current task. |
| Resolved Markdown, or JSON `status = "resolved"` | Follow the returned content in order. It already includes the shared procedure and applicable dynamic additions; do not reload every source file or add inactive branches. |
| Markdown headed `Powerspec skill resolution pending`, or JSON `status = "pending"` | Resolve only the reported missing choices, supply the answers as directed, and rerun the same lookup before following dependent instructions. |
| Nonzero exit, unavailable command, malformed or unexpected output | Report the failure. Do not interpret it as `null`, use partial output as resolved guidance, or silently bypass resolution. |

For pending choices, reuse explicit answers already supplied for this task. Otherwise ask the user, presenting any suggested default as a suggestion. Silence and elapsed time are not answers. A value already resolved from configuration or defaults needs no confirmation.

The command is non-interactive: pending questions arrive on stdout for the agent to present. Do not pipe answers or hook-event JSON into stdin. A question with no answer location has no owning consumer; report that configuration is needed for a rerun rather than writing a guessed file or repeatedly issuing the unchanged command.

Follow the result's answer-location instructions. An answer location's `#vars` or `#_change.<name>` suffix identifies a TOML table, not part of the filename. For temporal answers in the owning gitignored `openspec/.pspec/current.toml`, use direct `[_change."<name>"]` keys for choices exclusive to the active change, or `[vars]` for shared choices. Quote and escape the exact change name as a TOML key; do not introduce a nested `vars` table. Preserve other values and change tables. Persistent preferences belong in the same table structure in tracked `openspec/.pspec/config.toml` only when that persistence is intended. Use the owning consumer identified by resolution; do not invent a configuration location when lookup cannot identify one. Compile-time configuration errors require a configuration correction, not a runtime prompt.

Rerun after relevant inputs change. Retry a failed lookup after correcting its cause; if it remains unavailable, report the affected skill step as unresolved and continue independent work where possible. Skill installation and repair are separate from lookup and remain managed through ZuAT.

## Return to the selected workflow

Use the selected skill within its own scope and the user's task. Successful lookup is not evidence that the skill ran or its checks passed. Installing this skill alone does not establish native delivery; `pspec init --agent <current-agent>` separately provisions supported user-level hook registrations through ZuAT.

Automatic bootstrap reminders belong to `sessionStart` and `afterCompaction`. Do not add per-prompt or pre/post-tool hooks, run doctor as a precondition for each lookup, or poll readiness on every invocation. Installation, `pspec upgrade`, and diagnosis are separate requested operations; `upgrade --force` explicitly permits replacement of selected conflicting skills and is not a lookup fallback.

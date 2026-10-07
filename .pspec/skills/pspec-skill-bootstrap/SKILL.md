---
name: pspec-skill-bootstrap
description: Explain the conditional Powerspec content handoff for an already native-selected dynamic skill.
---

# Resolve dynamic content after native selection

Use the agent's native skill integration to discover and select a skill. Ordinary skills need no Powerspec call. This helper is ordinary too: follow it directly.

When generated guidance identifies a skill as dynamic, or its selected entrypoint declares a pspec.toml, obtain that exact selected location from the native integration. Do not substitute a catalog authoring path, search other installed copies, or guess user/project precedence.

From the task working directory, run:

```text
pspec resolve skill --path "<selected-directory-or-SKILL.md-or-pspec.toml>" --agent <current-agent>
```

The path identifies the skill; the working directory identifies the project's configuration. Add `--change <name>` only for an explicitly active change and retain the path, agent, and change on reruns. Use `--json` for structured results. Missing native-selected locations are missing handoff inputs; Powerspec does not discover them.

## Follow the result

- Resolved Markdown or JSON status `resolved`: follow the returned content in order. It is already assembled; do not recursively resolve it or load every branch.
- `Powerspec skill resolution pending` or JSON status `pending`: obtain only missing answers, preserve existing explicit answers, and rerun the displayed invocation. Suggestions, silence, and elapsed time are not answers. No procedural content is available yet.
- Successful literal `null`: the supplied selected copy has no manifest. Follow its ordinary native entrypoint. This supports version differences and does not require probing other ordinary skills.
- Nonzero exit, unavailable executable, or invalid output: report the failure; do not treat it as null, use partial instructions, or silently bypass dynamic resolution. Continue independent work when possible.

## Supply pending answers

Resolution is non-interactive and does not read stdin or write answers. Use the reported owning answer location. Its `#vars` or `#_change.<name>` suffix selects a TOML table, not a filename. Put temporary shared answers in `[vars]` and change-specific answers in `[_change."<name>"]` of that consumer's ignored current.toml, quoting and escaping the exact change key. Preserve other values and tables. Persistent preferences belong in config.toml only when persistence is intended. Without an owning answer location, report the missing configuration rather than inventing a file.

## Keep lifecycle actions separate

Successful content assembly does not mean a workflow ran. Provisioning remains a separate requested `pspec init --agent <current-agent>` operation; updates use the normal upgrade lifecycle. Do not install or repair skills as a content-resolution fallback or add per-prompt/tool callbacks. Targeted reminders arrive with their owning guidance at supported startup and compaction boundaries.

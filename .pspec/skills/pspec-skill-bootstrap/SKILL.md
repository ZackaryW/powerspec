---
name: pspec-skill-bootstrap
description: Retrieve one Powerspec skill when the user requests pspec:skill or applicable scenario guidance calls for that target, and handle dynamic content for an already native-selected skill.
---

# Retrieve the skill needed by the current task

This helper is ordinary and natively discoverable: follow it directly without resolving it. Choose the route from the task's actual request or applicable guidance.

Applicable configured guidance can trigger retrieval; the user need not name the skill again. The owning guidance defines when its scenario applies and any permitted fallback; this helper handles content handoff. Merely seeing a scenario rule or profile selection does not make that scenario active. Do not enumerate, load, or resolve all configured skills.

## Catalog target: pspec:<selector>

When the user requests `pspec:<selector>` or the current task matches a configured rule calling for it, remove only the `pspec:` prefix and run from the task working directory:

```text
pspec resolve skill --ref "<selector>" --agent <current-agent>
```

For example, `pspec:pspec-tdd` uses `--ref pspec-tdd`; `pspec:@builtin/pspec-tdd` uses that exact qualified reference. Do not remove the `pspec-` part of a declared name or manufacture a path. Lookup searches only the consumer's effective selected profiles, including `resolve-skills`. It returns ordinary catalog procedures as well as dynamic ones without installing them.

Use the returned canonical source directory as the base for relative references, scripts, and assets. Read supporting files only when the active procedure needs them. Retrieve another skill when its own scenario or an active dependency requires it; leave other selected skills deferred. This is not a one-skill-per-session limit.

## Native-selected dynamic target

For ordinary native invocation, use the agent's native skill integration to discover and select a skill. Ordinary native skills need no Powerspec call.

When generated guidance identifies a skill as dynamic, or its selected entrypoint declares a pspec.toml, obtain that exact selected location from the native integration. Do not substitute a catalog authoring path, search other installed copies, or guess user/project precedence.

From the task working directory, run:

```text
pspec resolve skill --path "<selected-directory-or-SKILL.md-or-pspec.toml>" --agent <current-agent>
```

The path identifies the skill; the working directory identifies the project's configuration. Missing native-selected locations are missing handoff inputs; Powerspec does not discover them or substitute a catalog target. For either route, add `--change <name>` only for an explicitly active change. Retain the same task directory, agent, explicit change and selected path or concrete returned reference on reruns. Use `--json` for structured results.

## Follow the result

- Resolved Markdown or JSON status `resolved`: follow the returned content in order. It is already assembled; do not recursively resolve it because an entrypoint contains native handoff instructions, or load inactive branches and sibling procedures.
- `Powerspec skill resolution pending` or JSON status `pending`: obtain only missing answers, preserve existing explicit answers, and rerun the displayed invocation. Suggestions, silence, and elapsed time are not answers. No procedural content is available yet.
- Successful literal `null`: the supplied selected copy has no manifest. Follow its ordinary native entrypoint. This supports version differences and does not require probing other ordinary skills.
- Nonzero exit, unavailable executable, or invalid output: report the failure; do not treat it as null, use partial instructions, or silently bypass dynamic resolution. Continue independent work when possible.

For ambiguity, present the returned exact references rather than guessing. A missing consumer, unselected target, unavailable source, or broken manifest remains a failure without native-copy substitution or ordinary-content fallback. A catalog ordinary skill returns resolved content, never path-style null.

If the owning guidance explicitly permits a fallback when a skill or its tooling is unavailable, report the limitation and continue that permitted work. For example, the standing memory rule permits Git and current repository evidence when memory lookup is unavailable. This does not authorize following an unresolved dynamic procedure or claiming that memory verification or skill execution occurred.

## Supply pending answers

Resolution is non-interactive and does not read stdin or write answers. Use the reported owning answer location. Its `#vars` or `#_change.<name>` suffix selects a TOML table, not a filename. Put temporary shared answers in `[vars]` and change-specific answers in `[_change."<name>"]` of that consumer's ignored current.toml, quoting and escaping the exact change key. Preserve other values and tables. Persistent preferences belong in config.toml only when persistence is intended. Without an owning answer location, report the missing configuration rather than inventing a file.

## Keep lifecycle actions separate

Successful content assembly does not mean a workflow ran or expand the user's scope and authorization. Provisioning remains a separate requested `pspec init --agent <current-agent>` operation; updates use the normal upgrade lifecycle. Do not install or repair skills as a content-resolution fallback or add per-prompt/tool callbacks. Targeted reminders arrive with their owning guidance at supported startup and compaction boundaries.

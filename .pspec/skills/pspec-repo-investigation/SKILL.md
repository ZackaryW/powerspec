---
name: pspec-repo-investigation
description: Investigate repository evidence and resolve material feasibility uncertainty before dependent design or implementation. Use for architecture understanding, targeted change impact, or a bounded technical experiment; skip when the task is already evidence-complete.
---

# Investigate repository evidence and feasibility

Establish the concrete question, the repository boundary, and the evidence needed by the caller. Preserve explicit tool constraints, accepted answers, the active decision policy, and the authority already granted for the task. Use the caller's conversation or artifact for findings; do not create a separate investigation or prototype document by default.

When `pspec-skill-bootstrap` is active, follow its lookup and error handling. A normal installed copy of this skill may return `null` from `pspec resolve skill` because it has no dynamic manifest; in that case, use this skill directly.

## Choose an evidence route

Inspect repository instructions and the tool interfaces actually exposed to the agent. Select a route from the question and usable repository support:

- For broad architecture, cross-module dependencies, or system-wide behavior, prefer CodeGraph when the repository already has a `.codegraph/` index and a usable CLI or MCP interface. Use the interface's current help or schema. Do not create or refresh an index unless the user separately requests it.
- For a bounded feature, bug, symbol, caller, test, or localized impact question, prefer Ripwire when its CLI or MCP interface can read the repository. Ripwire does not require a made-up repository marker; consult the installed interface rather than inventing commands.
- With only one suitable tool, use it and supplement its gaps with focused search and source reading. An MCP interface can be usable without a local executable.
- With neither tool, continue with ordinary search, source inspection, tests, configuration, and version-control evidence. Do not install tools merely because this skill was selected.

Do not run both tools by default. Broaden or switch routes when the task expands or the remaining uncertainty warrants it. Treat an index marker or successful command as evidence of availability, not freshness, completeness, or total understanding. Check material findings against relevant source, tests, configuration, or another current observation. If a query fails or appears stale, state the limitation and continue through an available route.

## Assess feasibility

Separate observed facts, historical guidance supplied by the caller, assumptions, and experimental observations. Focus on uncertainty that could change the design, scope, sequencing, or viability of dependent work.

If current evidence settles the question, record the conclusion and return to the caller. Do not manufacture a prototype.

If material uncertainty remains, define the smallest useful experiment:

- the question it answers;
- the narrow scope and disposable or reversible setup;
- observable evidence for success and failure;
- the dependent work that should wait for the result.

For planning-only work, describe the experiment without executing it. When the user's current request already authorizes the experiment, run it without asking for the same permission again and report actual observations and limitations. Continue independent investigation while a dependent choice remains unresolved.

## Return findings

Report the answer to the original question, the evidence that supports it, material coverage limits, and any remaining assumption or experiment. Keep environment maintenance and simple edits proportionate: do not force feasibility work, a utility plan, TDD, or BDD when no material uncertainty exists.

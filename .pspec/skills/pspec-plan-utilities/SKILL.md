---
name: pspec-plan-utilities
description: Plan utility responsibilities, reuse decisions, public contracts, and focused verification for an accepted software change. Use when designing or revising reusable implementation boundaries; this segment plans work without implementing it.
---

# Plan utilities

Produce the utility portion of an accepted design. Keep application decisions and wiring with their owning feature. When bootstrap supplies resolved skill content, follow that content and its handling of pending choices or errors.

## Establish the scope

Use the behavior and constraints already agreed with the user or calling workflow. Read the relevant specifications, implementation, tests, dependency declarations, and existing design before proposing boundaries. Reuse a current plan where its contracts still fit; revise only responsibilities affected by the change.

Use the project, output destination, and edit scope supplied by the task. Return the plan directly when no document is requested; no particular planning system or artifact layout is required.

First determine whether reusable implementation work is needed. Environment setup, documentation, or configuration edits without behavioral effects do not need a utility plan. For mixed work, assess only the relevant implementation portion. If existing behavior or declarative configuration already satisfies the request, explain that briefly when an assessment was requested; do not manufacture utilities, prompts, tests, or a separate not-applicable artifact.

## Assess reuse before custom mechanics

Derive responsibilities from the required behavior, then inspect existing project and dependency APIs that might fulfill them. Record concrete fit or mismatch using current signatures, constraints, and relevant implementation or documentation. An API name or an old governance example is not evidence that the required capability exists in the current version.

Choose among direct reuse, extending an existing owner, or introducing a focused utility. Prefer direct calls where an existing API already provides the contract. A wrapper should add a meaningful boundary, adaptation, or policy; merely renaming a dependency call is not a new responsibility. Do not recreate a dependency's ownership, rollback, storage, or routing machinery without a demonstrated gap.

Keep feature-specific decisions with the feature. A single current caller can justify a utility when it isolates a meaningful responsibility, but hypothetical future reuse does not justify a general framework. State the remaining application work even when no new utility is needed.

## Define the necessary contracts

For each utility that the accepted behavior needs, record:

- **Responsibility and owner:** what it does, who calls it, and its proposed module or existing home.
- **Public contract:** signature or equivalent interface, inputs, outputs, and relevant validation rules.
- **Effects and failures:** reads or writes, resource lifetime, error outcomes, and repeated-invocation behavior where relevant. Do not promise atomicity or rollback without support.
- **Reuse decision:** the existing API being used or extended, or the concrete reason custom work is needed.
- **Verification boundary:** the smallest meaningful check of its observable contract, plus integration work it cannot establish alone.

Use the configured utility location when supplied; otherwise follow the project's existing structure. Organize modules by responsibility. Keep utility behavior independent of CLI parsing and presentation where those are caller concerns. Do not create empty utility folders, scaffold code, or move unrelated implementation merely to conform to the plan.

Resolve material uncertainty from available evidence or the user's decision before planning dependent implementation as settled. Preserve decisions already made, identify remaining assumptions, and continue independent planning where possible. A plan consistent with the user's authorized scope does not need a new approval ceremony solely because this skill was used.

## Plan verification at the real boundary

Use focused cases for pure transformations and data matrices. For filesystem, process, packaging, installation, or external-service behavior, identify the integration boundary that must actually be exercised and the isolated fixtures it needs. Mock-call counts alone cannot prove persistent effects or restoration behavior.

Reuse existing tests and harnesses when they cover the intended contract. Separate utility evidence from application wiring and composed behavior: a passing parser test does not prove the CLI uses that parser correctly. Plan affected checks first, broadening for shared dependencies, unresolved risks, and required project checks rather than scheduling the full suite after every increment.

Describe expected outcomes and relevant failure cases; do not run a fabricated red/green cycle to populate a planning record. Read-only investigation can establish API fit, but mark proposed verification as planned until it has actually run.

## Return the plan to its caller

Put the assessment and necessary contracts in the caller's existing design or requested artifact. Use a separate utility-plan file only when the caller requests one or the detail warrants it, and link it from the owning design. Otherwise return the assessment directly. Avoid parallel copies of the same contract.

Summarize reuse decisions, planned utility slices, unresolved choices, and remaining application/integration work. Keep implementation tasks pending and return the plan to the user or caller.

When implementation is authorized later, the caller can hand the selected contracts to pspec-tdd or another chosen development process. Planning utilities does not require that skill to be installed and does not activate TDD or BDD itself.

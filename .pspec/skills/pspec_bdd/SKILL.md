---
name: pspec-bdd
description: Shape and verify selected behavior through BDD features rooted in OpenSpec scenarios. Use when the user or calling workflow selects a bounded acceptance-testing segment, including reconciling existing features with their behavioral source.
---

# Behavior-driven development from OpenSpec scenarios

OpenSpec requirements and their behavioral scenarios define the intended behavior. BDD features make selected scenarios executable; step implementations and test runs provide evidence. Adding an executable feature does not transfer ownership of the behavior out of OpenSpec.

Use this skill for the accepted segment of work. It does not automatically activate a repository-wide BDD policy, select a framework, advance an OpenSpec operation, archive, or commit. When bootstrap supplies resolved skill content, follow that content and its handling of pending choices or errors.

## Establish the behavioral source

Identify the owning OpenSpec root, capability, requirement, and relevant scenarios. Use the current canonical spec together with the selected change's accepted delta. Treat proposed or unresolved behavior as a decision to settle, not an established requirement. An active delta changes only its stated scope; unrelated canonical behavior remains applicable.

Read the actual scenario conditions and outcomes. A reference-only placeholder pointing to a feature is a trace link, not a behavioral scenario. If that is all that exists, identify the gap and use the requirement, existing feature, and available decisions to propose the missing scenario. Confirm material ambiguity before dependent implementation; passing existing tests alone does not authorize their behavior.

Keep behavioral scenarios in OpenSpec when adding BDD coverage. Do not delete them or replace them with proof-only placeholders to avoid repeated wording. Features may concretize examples, fixtures, and interactions, but may not independently add, weaken, or redefine the intended outcome. If execution reveals a missing product decision, settle it in the owning specification before treating it as required behavior.

When a repository explicitly uses a different ownership policy, identify that conflict and obtain direction before migrating its artifacts. Creating or installing this skill does not silently rewrite repository governance.

## Select the verification boundary

Choose the smallest meaningful boundary that proves the scenario's observable outcome. Keep pure transformations and exhaustive data matrices in focused tests when those tests suffice. Use BDD where a composed interaction or acceptance example benefits from executable representation. An OpenSpec scenario does not require a feature file merely because it exists.

For mixed work, distinguish utility contracts from the composed outcome. Utility tests support the journey but do not establish integration behavior they never exercise. Reuse useful existing tests and harnesses; avoid adding duplicate tests solely to assign each workflow its own proof.

Environment-only maintenance, documentation, and configuration work without behavioral effects need appropriate validation, not a manufactured BDD journey. Planning a feature or mapping existing evidence does not by itself authorize implementation.

## Shape executable examples

Use the project's selected framework, test layout, and runner. Establish missing choices from configuration or the accepted scope before asking. Keep language and framework mechanics in their own resources when such branches are added; this shared procedure does not prescribe Flutter, Behave, pytest-bdd, or Cucumber.

Translate the source conditions and expected outcome into concrete examples. Make initial state and triggering action discoverable, whether in explicit Given/When steps or an existing readable harness. Assert public outputs, visible state, or externally observable effects through the relevant production path. Fixtures can control external dependencies without substituting the behavior being verified.

Retain a direct trace from each executable scenario to its OpenSpec root, capability, requirement, and source scenario. Reuse existing stable identifiers or binding conventions. Where no convention exists, a nearby source path plus exact requirement/scenario headings is sufficient; do not introduce a registry or permanent checker just for this mapping.

One source scenario may have several executable examples or verification layers. A shared journey may cover several source scenarios when the mapping states which assertions establish each outcome. Do not force a one-to-one file layout or duplicate a journey under multiple names for coverage counts. A requirement-level link alone is insufficient to claim every scenario is covered.

For an example of the boundary and mapping, read [Scenario to executable feature](references/scenario-to-feature.md).

## Verify the selected behavior

For a new or changed behavior under implementation, make the intended acceptance example fail for the missing behavior before implementing that increment where feasible. Undefined steps, failed generation, missing tools, and broken fixtures are setup failures, not evidence of the intended failure. Do not remove working implementation to reconstruct a historical fail-first sequence.

Implement or adapt the steps and accepted behavior, then run the affected executable scenarios through the established runner. Inspect what the assertions actually prove. A feature binding, generated test file, successful generator, or count of passing scenarios is not evidence by itself that the intended behavior was exercised.

Start with the affected features and dependencies. Broaden verification when shared changes, failures, required project checks, or unresolved concerns justify it; do not run the full suite after every small edit by default. Follow the repository's generation rules when applicable rather than assuming generation can safely be narrowed in the same way as test execution.

## Reconcile source, examples, and evidence

Keep the distinction clear: OpenSpec describes intended behavior, features encode executable examples, and recorded runs establish what was actually verified. Similar wording across these layers is acceptable when it preserves a single direction of authority.

When they disagree, identify the discrepancy and its owning source. Correct a stale feature to match accepted behavior; route a genuine behavior change through its OpenSpec scenario. Do not automatically overwrite either side based on timestamps or whichever test currently passes. Preserve useful unbound tests while reporting their missing or unresolved source rather than inventing authority.

When a change is merged or archived by its calling workflow, keep source references usable against the resulting canonical scenario. Update affected paths or renamed headings as part of that lifecycle; do not retain an active-change path as the only trace after it moves. This skill reports needed reconciliation and does not initiate archive itself.

Return the source scenarios, their executable examples or other selected checks, commands actually run, observed results, and remaining gaps. Distinguish planned, implemented, passed, failed, and not-run evidence. A passing example establishes only the behavior its assertions cover; it does not automatically complete its whole requirement or change.

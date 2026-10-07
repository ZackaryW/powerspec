---
name: pspec-bdd
description: Shape and verify selected behavior through executable BDD examples rooted in OpenSpec-owned scenarios. Use for a bounded behavior-testing segment or to reconcile existing features with their authoritative scenarios.
---

# Behavior-driven development from OpenSpec scenarios

OpenSpec owns all behavioral scenarios. BDD features are executable examples of those scenarios; step implementations and test runs provide evidence. Features, issues, conversations, and design notes do not form alternative scenario authorities. Record accepted behavioral decisions in the owning OpenSpec scenarios before treating them as the contract for executable coverage.

Use this ordinary skill directly through the native integration within the requested scope.

## Establish the intended behavior

Identify the owning OpenSpec root, capability, requirement, and scenarios. Read the canonical specification together with the selected change's accepted delta, relevant user decisions, existing examples, and affected implementation. An accepted delta changes only its stated scope; unrelated canonical behavior remains applicable.

Follow the consumer's OpenSpec store routing, including a spawned workset's branch-specific store. The owning specification may reside outside the implementation repository. Do not create a second local scenario authority merely because the consumer has no local `openspec/specs` copy; preserve the owning store identity in scenario references.

Distinguish settled behavior from assumptions and unresolved product decisions. Use available evidence and prior answers before asking about material ambiguity. Passing existing tests alone does not make their behavior an accepted requirement.

Keep behavioral scenarios in OpenSpec when adding executable coverage. Do not delete them or replace them with reference-only placeholders pointing to features. Features may concretize data and interactions but may not independently add, weaken, or redefine intended outcomes. If an existing feature has no owning OpenSpec scenario, identify that gap and establish the accepted scenario in OpenSpec within the authorized scope; otherwise report the missing source as pending. Preserve useful tests while reconciling their ownership.

## Select the verification boundary

Choose the smallest meaningful boundary that proves the observable outcome. Keep pure transformations and exhaustive data matrices in focused tests when those suffice. Use BDD where a composed interaction or acceptance example benefits from executable representation; not every requirement needs a feature file.

For mixed work, distinguish utility contracts from the composed outcome. Utility tests support a journey but do not establish integration behavior they never exercise. Reuse useful tests and harnesses instead of duplicating them to assign each process its own proof.

Environment-only maintenance, documentation, and configuration edits without behavioral effects need appropriate validation rather than a manufactured BDD journey. Planning examples or mapping evidence does not by itself authorize implementation.

## Shape executable examples

Use the project's selected framework, test layout, and runner. Establish choices from configuration and accepted scope before asking. The shared procedure does not prescribe a language or framework.

Translate conditions and expected outcomes into concrete examples. Make initial state and triggering action clear through Given/When/Then or the existing readable harness. Assert public outputs, visible state, or externally observable effects through the relevant production path. Fixtures may control external dependencies without replacing the behavior being verified.

Retain a direct trace from each executable scenario to its OpenSpec root, capability, requirement, and source scenario. Reuse stable identifiers or binding conventions when present; otherwise a source path plus exact requirement and scenario headings is sufficient. A feature is never its own authoritative behavioral source.

One accepted scenario may need several examples or verification layers. A shared journey may cover several outcomes when its assertions clearly establish each. Avoid forcing a one-to-one file layout or duplicating journeys for coverage counts. A broad requirement link alone does not prove every outcome is covered.

For an illustrative mapping, read [Scenario to executable feature](references/scenario-to-feature.md).

## Verify the selected behavior

For new or changed behavior under implementation, make the intended acceptance example fail for the missing behavior before implementing that increment where feasible. Undefined steps, failed generation, missing tools, and broken fixtures are setup failures. Do not remove working implementation to reconstruct a historical fail-first sequence.

Implement or adapt the steps and authorized behavior, then run the affected scenarios through the established runner. Inspect what the assertions prove. A binding, generated test file, successful generator, or count of passing scenarios is not by itself evidence that the intended behavior was exercised.

Start with affected features and dependencies. Broaden verification when shared changes, failures, required project checks, or unresolved concerns justify it. Follow the project's generation rules; generation may not be safely narrowed in the same way as test execution.

## Reconcile examples and evidence

Compare the owning OpenSpec scenarios, executable examples, and observed results. Correct stale examples to match accepted scenarios. Resolve genuine behavior changes with the task's owner and record them in OpenSpec before updating dependent coverage. Do not automatically overwrite a source based on timestamps or whichever test currently passes.

Preserve useful existing tests while reporting missing or unclear OpenSpec scenario mappings. Keep references accurate when their source moves or is renamed, including when accepted change scenarios become canonical. This skill does not initiate archival or another workflow stage.

Return the behaviors covered, their examples or other selected checks, commands actually run, observed results, and remaining gaps. Distinguish planned, implemented, passed, failed, and not-run evidence. A passing example establishes only the behavior its assertions cover. Return control to the user or caller when the selected segment is complete.

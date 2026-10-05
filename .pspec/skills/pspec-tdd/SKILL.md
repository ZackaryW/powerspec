---
name: pspec-tdd
description: Develop selected software behavior through observed red, green, and refactor cycles. Use when the user or calling workflow selects a bounded TDD segment.
---

# Test-driven development

Use the project's established test tools for one selected development segment.

When pspec-skill-bootstrap supplies resolved content, follow it in order. [pspec.toml](pspec.toml) declares language-specific additions and where they belong in this shared procedure. Follow bootstrap's handling of pending choices and errors; neither means permission to bypass resolution.

For direct use without bootstrap, consult [pspec.toml](pspec.toml) version 2: `section` names an exact destination heading in this document, `pos = "after"` adds content after that section and its descendants, and `source_section` selects a heading and its descendants in the source file. `pos = "replace"` replaces the entire destination section. Establish the language and any inputs required by the selected additions from configuration or accepted scope; ask only for unresolved choices. Substitute declared values once into the selected text before following it. The bundled language resource currently covers Python; report a missing selected language resource rather than inventing a branch or silently omitting it.

## Scope and expected behavior

Take the requested behavior, accepted constraints, and test environment from the user or calling workflow. This segment does not establish a repository-wide TDD policy or activate a surrounding development process.

Identify the expected outcome, the public boundary where it is observable, and a meaningful example. Resolve material ambiguity from available evidence or the user's decision, preserving choices already settled.

During planning, describe the behavior, expected failure, and verification approach. Planning alone does not authorize implementation. For changes without behavioral effects, such as environment-only maintenance, use appropriate validation and return to the caller without manufacturing a TDD cycle.

Preserve existing implementation and user-authored work. Keep the segment within its authorized scope. When delegated only utility implementation, leave application wiring and integration work with the caller.

## Red: observe the missing behavior

Write a focused test expressing the intended outcome and run it before changing production behavior. Confirm it fails because the required behavior is missing. Syntax errors, missing dependencies, and broken test setup do not establish the intended red result.

If the test already passes, determine whether the behavior exists or the test fails to distinguish the change. Do not break working code to manufacture red. For a regression, reproduce the defect with a failing test when possible.

When joining work in progress, preserve existing implementation and distinguish tests added afterward from an observed test-first cycle. Begin TDD with the next appropriate behavior increment rather than deleting work to recreate an earlier stage.

## Green: implement the increment

Implement enough behavior to satisfy the failing test within the accepted scope. The test establishes evidence for this increment; it does not replace other accepted requirements.

Run the focused test and checks directly affected by the change. Broaden verification when dependencies, failures, or unresolved concerns warrant it. Do not run the full suite after every small increment solely because another TDD cycle occurred; still complete checks required by the project or calling workflow.

Observe actual outcomes at the affected public boundary. For persistent effects, use isolated fixtures and verify the resulting state. Internal mock-call counts alone do not establish externally observable behavior.

## Refactor and repeat

Once relevant checks pass, improve naming, structure, and duplication where useful without expanding the behavior contract. Rerun affected checks after changes; investigate failures before proceeding.

Return to red for the next accepted behavior increment. Finish the cycle when the requested segment is complete. If progress depends on an unavailable environment or an unresolved decision, report that condition instead of claiming completion.

## Return evidence to the caller

Report the implemented behavior, checks actually run, observed results, and unresolved work. Distinguish an observed red-to-green cycle from tests added after implementation. Separate implementation failures from environment limitations; do not infer execution from test files or claim verification on an unavailable platform.

For a utility-only segment, identify the utility behavior verified and leave application wiring and integration verification explicitly pending. Passing utility tests does not establish completion of the entire feature. Reuse earlier evidence only while it still covers the current implementation and conditions.

Return the evidence and remaining work to the user or caller. Completing this segment does not initiate another development or release step.

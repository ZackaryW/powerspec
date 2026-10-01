---
name: pspec-smarter-decision
description: Assess unresolved task choices and decide whether to infer, recommend, or ask under an autonomous, balanced, or exhaustive decision policy. Use when ambiguity affects a requested design, investigation, or implementation.
---

# Assess unresolved decisions

Control the amount of user involvement in decisions within the accepted task. Preserve the user's scope, explicit choices, and prior answers. This skill does not select a development process or authorize implementation, publication, or external actions.

When bootstrap supplies resolved content, follow it and its handling of pending choices or errors. The manifest selects only the effective decision policy. For direct use without bootstrap, use the supplied decision_level, or balanced when none is supplied, and read only the matching file under modes/. Accepted user instructions can select another level; do not silently substitute a default for an invalid configured level.

## Establish what is unresolved

Read the relevant request, accepted decisions, and available project evidence before asking. Distinguish a missing fact that can be investigated from a preference only the user can settle. Existing code is evidence of current behavior, not permission to contradict an explicitly requested redesign.

Identify the concrete choice, its affected work, and the cost of changing it later. Preserve decisions already settled unless new evidence conflicts with them; explain that conflict instead of repeatedly reopening the same question. Continue independent investigation or authorized work while a dependent decision remains unanswered.

## Decision policy

For direct use, read [autonomous](modes/autonomous.md), [balanced](modes/balanced.md), or [exhaustive](modes/exhaustive.md) according to decision_level. Apply only that policy. Powerspec resolution replaces this section with the selected policy's content.

## Carry the decision forward

Apply accepted answers to the affected work and state non-obvious assumptions briefly where they help the user assess the result. Use the caller's existing conversation or artifact; do not create a separate decision document by default.

A question is answered only by an actual user response or existing explicit instruction. A suggested or preselected option, silence, and elapsed time do not settle it. Reuse answers on reruns and after compaction; a mode change affects remaining decisions rather than reopening completed ones automatically.

Return to the requested work after the decision. The selected level changes how uncertainty is handled, not the task's authority, scope, or completion evidence.

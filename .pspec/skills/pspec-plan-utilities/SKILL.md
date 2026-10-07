---
name: pspec-plan-utilities
description: Identify and plan generic helpers that an accepted change needs and other projects could reuse. Assess existing libraries, define portable contracts, and plan focused verification before application integration.
---

# Plan reusable helpers

Produce the generic helper portion of an accepted design. A utility must be usable in another project without carrying this application's models, configuration layout, or workflow rules with it.

## Find the reusable mechanics

Read the accepted requirements, relevant code, dependencies, tests, and current design. Identify the underlying operations needed by the change, then separate their mechanics from the application's decisions.

For example, finding the nearest matching file within a supplied directory boundary can be a utility. Deciding which project configuration owns a session belongs to the application. Traversing a dependency graph can be a utility; composing the application's profiles remains application logic.

For each candidate, check:

- Can another project call it with ordinary values, paths, mappings, or a small explicit interface?
- Can its tests describe its behavior without importing application models or reproducing the application's folder conventions?
- Can you name a concrete use outside this project that fits the same contract?
- Does it solve a present requirement without adding speculative modes or a general framework?

Inputs should supply the paths, names, ordering, timeouts, and callbacks that genuinely vary between callers. Keep application policy in the caller. Do not turn every constant into an option or rename application concepts to make them appear generic.

A single current caller can justify a portable helper. Multiple internal callers alone do not make a domain service a utility. Keep domain parsing, application workflows, and feature-specific decisions in their own modules.

## Assess existing implementations

Inspect current project and dependency APIs before proposing custom code. Record their actual fit using signatures and behavior. Prefer a direct call when a library already supplies the needed contract. An adapter is useful when it supplies missing behavior, such as bounded discovery or error handling; a wrapper that only renames a function adds no reusable capability.

Start with existing helpers, the standard library, and installed dependencies. For substantial mechanics such as validation, parsing, or graph processing, also inspect relevant mature third-party packages before designing a replacement. Verify public APIs against the required behavior and supported version. Assess maintenance, compatibility, dependency cost, and licensing where they affect adoption; popularity alone does not establish fit. Keep the investigation proportional to the helper and avoid repeating settled research without new evidence.

Record the choice and the evidence that matters: direct reuse, a small adapter for a specific gap, or custom implementation because the alternatives do not fit. Package inspection does not authorize installation, dependency migration, or speculative abstractions. Keep application-specific models and policy in application code even when a package implements their validation or execution mechanics.

Explain a concrete gap before replacing a dependency's mechanics. Preserve native ownership of acquisition, installation, storage, and routing. Reuse suitable helpers already present, and do not invent utility work for environment, documentation, or configuration changes without behavioral effects.

## Describe each helper

Use a short entry for each necessary helper, with enough detail to review it independently:

- **Purpose and portability:** the generic operation, the current caller's need, and an example from another project.
- **Contract:** proposed signature, inputs, output, ordering, and validation. Avoid application-specific argument or result types.
- **Effects and failures:** reads/writes, resource lifetime, errors, and relevant repeat-call behavior. State only supported atomicity or rollback guarantees.
- **Reuse:** the existing implementation to call or extend, or the concrete gap that requires a new helper.
- **Verification:** focused examples and failure cases that exercise the portable contract.

Use the configured utility location or the project's established equivalent. Helpers may remain local while being designed for reuse; do not create a new package or publish a library unless requested. Do not create empty folders or scaffold implementations during planning.

After the helper entries, briefly describe how application code will supply policy and consume their results. Keep that integration work explicit instead of placing it in the utility list.

## Order implementation and verification

Plan each helper with its relevant tests as a coherent slice. Implement and verify the required helpers before application code that depends on them. Use domain-neutral fixtures for helper tests, then separately verify application behavior through real callers.

Filesystem and process helpers need isolated integration fixtures that observe actual results and failures. Internal mock-call counts alone do not prove persistent effects. Start with affected checks and broaden when dependencies or unresolved risks justify it.

Planning does not activate implementation or a testing workflow. Describe proposed evidence as planned; do not claim a red/green cycle or create implementation just to complete the plan.

## Return the plan

Use the caller's existing design or requested destination. Otherwise return the plan directly. Avoid a parallel document unless requested or justified by the detail.

Summarize helpers to reuse or build, application work that consumes them, and unresolved decisions. If no generic helper is needed, say so and leave the implementation with its application owner. Keep implementation tasks pending. The caller may later hand accepted helper contracts to TDD or another selected process.

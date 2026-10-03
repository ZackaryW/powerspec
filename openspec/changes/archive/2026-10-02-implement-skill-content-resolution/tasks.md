# Tasks

Prerequisite: establish-profile-consumer-resolution. Production provisioning, hooks, and remote acquisition are not required for this milestone. The checked item below is source authorship carried forward from original task 4.1, not evidence of runtime behavior.

## 1. Manifest and input resolution

- [x] 1.1 Parse version 1 skill manifests with entrypoint, typed inputs/parsers, equality guards, hints, and dynamic section/pos/path/source_section fields; verify invalid versions/types/placements, unknown references, and dependency cycles produce resource-specific diagnostics.
- [x] 1.2 Evaluate only reachable inputs using consumer layers and skill value defaults; verify valid values skip prompts/hints, invalid values fail without fallback, known false branches request no dependent inputs, missing controlling/path values remain pending, and unrelated skills are not evaluated.
- [x] 1.3 Implement repeated-ID hint groups and scalar default_hint; verify first matching typed detector supplies only a suggestion, no-match behavior retains the prompt default, and hints neither persist nor count as answers.
- [x] 1.4 Document value defaults versus prompt/hint suggestions and guarded Python tooling; run the documented cases as focused input fixtures, including non-Python branches requesting no Python tooling.

## 2. Dynamic document composition

- [x] 2.1 Parse exact unique Markdown section boundaries with fenced headings ignored; verify heading/body/descendant boundaries, optional whole-file source selection, and resource-specific missing/ambiguous selector errors.
- [x] 2.2 Assemble before/after additions in stable original document order with concise source labels and first-occurrence deduplication per canonical destination/position/file/section; verify shared TDD flow, multiple additions, and the same source at distinct destinations.
- [x] 2.3 Implement whole-section replace and ordered replace/combine accumulation; verify last-active wins including A/B/A, first-combine excludes original text, inactive entries, mixed resets/appends, retained-source deduplication, and reset of duplicate history.
- [x] 2.4 Implement ancestor replacement suppression and same-target surrounding placements; verify descendant before/after/replace/combine suppression in either declaration order, shared endpoint cases, inactive ancestor behavior, and no re-anchoring inside inserted content.
- [x] 2.5 Apply single-pass declared substitutions and canonical skill-root containment; verify unknown path variables, literal undeclared angle-bracket prose, path/symlink escapes, missing selected resources, inactive absent resources, and no recursive interpretation or partial success output.
- [x] 2.6 Document the dynamic-only manifest and placement interactions using passing fixtures; verify no static sequence, inline markers, old after key, or numbered insert syntax is required.

## 3. Installed lookup and CLI outcomes

- [x] 3.1 Pin ZuAT revision e42dbfe64f071da145dc33d728f92ef6edd1195b and add explicit-agent read-only installed inspection; verify the actual public API in disposable homes, no registry/observation writes, no implicit all-agent lookup, missing/unresolved identity diagnostics, native-selected user/project coexistence, and validated optional host-selected path evidence without a Powerspec scope policy.
- [x] 3.2 Implement src/powerspec/cli/skill.py using shared input and composition results; verify both pspec and powerspec, required agent syntax, optional explicit change and selected-path evidence, Markdown default, JSON content equivalence, literal null for no manifest, and stderr/nonzero errors without success payloads.
- [x] 3.3 Return pending questions with constraints, suggested defaults, answer locations, and same-agent/change rerun instructions; verify a manual scoped answer changes the next lookup without affecting another change, procedural content stays withheld, and lookup snapshots show no writes.
- [x] 3.4 Update command help and CLI tests for incremental readiness; verify skill no longer claims placeholder status while any still-unimplemented init/hook/sync/flush commands retain honest unavailable diagnostics and help/import/syntax paths remain side-effect-free.
- [x] 3.5 Document null/pending/resolved/error and unavailable-executable recovery; verify examples run through the real command and malformed manifests never use normal-skill fallback.

## 4. Reviewed bootstrap and TDD milestone

- [x] 4.1 Author pspec-skill-bootstrap and the global builtin profile; source inspection covers the explicit command, bootstrap exemption, result outcomes, unavailable executable, and distinction between installation and invocation. Carried forward from original task 4.1.
- [x] 4.2 Exercise pspec skill pspec-tdd --agent <agent> against a disposable complete installation using the authored consumer/profile; verify Python scope/red/green placement, preserved refactor/handoff, effective uv run pytest, no configured-value prompts or BDD questions, and normal entrypoint usability.
- [x] 4.3 Compare real resolved Markdown with docs/examples/tdd-python-resolution.md, update the example only for contract-consistent rendering, and record unsupported, pending, answered, broken, and environment-only cases with no automatic testing activation.
- [x] 4.4 Run relevant tests with uv run pytest and openspec validate implement-skill-content-resolution --strict; record the usable read-only command milestone without claiming packaging, hook delivery, sync, or flush completion.

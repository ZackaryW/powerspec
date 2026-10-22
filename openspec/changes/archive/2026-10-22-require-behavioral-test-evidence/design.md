# Design

## Context

See proposal.md for motivation. TDD's shared procedure lives in `.pspec/skills/pspec-tdd/SKILL.md`; its Python additions are inserted through existing manifest anchors. BDD is an ordinary skill with an OpenSpec scenario-to-feature reference. Both already require observable outcomes and proportional verification, but neither explicitly addresses implementation-text substitutes.

The Python CLI context already publishes verification planning to `rules.tasks` and TDD invocation guidance to `operations.apply.guidance`. Profile selection and the resolver are separate contracts; the Python CLI profile intentionally does not select BDD. Existing guidance tests exercise dispatch and publication but include assertions against authored prose. Resolver tests also use controlled fixture text to verify real selection and assembly behavior, which is a valid text contract.

This design is needed because the rule crosses two skill procedures and governance delivery, and must distinguish textual products from incidental implementation text.

## Goals / Non-Goals

**Goals:** Give test authors and reviewers an actionable evidence criterion; preserve legitimate text tests and existing meaningful coverage; deliver a short planning/apply reminder through established owners.

**Non-Goals:** Ban assertion operators, add a linter or mutation-testing dependency, impose mandatory mutation runs, activate BDD globally, audit every repository test, or prove agent compliance from delivered instructions. No generic helper is needed; existing skill resources, TOML attachments, resolver, and sync APIs suffice.

## Decisions

1. **Judge the claimed contract and observation boundary.** Before adding or accepting a test, identify what must work, where it is observed, and a plausible defect that makes the test fail. This is a short reasoning check, not a new report template or a requirement to mutate working code. A syntax-based ban on strings or regex would incorrectly reject CLI, parser, template, and serialization contracts.

2. **Put the procedure in each skill.** Add concise guidance and contrasting examples to TDD's shared scope/red/evidence sections and BDD's verification-boundary/example/evidence sections. Preserve TDD's existing heading anchors and Python dynamic placements. Update BDD's existing reference where useful rather than creating another guide. For example, finding `save(...)` in source does not establish persistence; invoking the relevant operation and checking its stored result does. Exact text remains valid when an accepted contract requires it.

3. **Keep governance small and owned by existing resources.** Extend `.pspec/contexts/python-simple-cli.toml` task-planning and apply attachments with the behavioral claim, observation boundary, and text-contract distinction. Do not create a global profile, copy full procedures into context, or hand-edit managed configuration. Publish through `pspec sync` during implementation and review its managed diff. Utility governance retains its existing delegation to TDD without another duplicate rule.

4. **Review only directly affected evidence.** Start with `tests/test_guidance_bodies.py`, `tests/test_skill_resolution.py`, and relevant document/CLI resolution tests if affected by the edits. Preserve controlled fixture markers that prove selection, ordering, inclusion, exclusion, and delivery. Replace incidental prose checks with assertions appropriate to the existing behavior: parsed publication structure, selected versus excluded contributions, and expected fixture content through production assembly. Do not replace every string assertion or remove real coverage to reduce brittleness. Do not compute expected results by copying the implementation's transformation.

5. **Verify this prose change without testing for its own keywords.** Semantically review both skills against the spec scenarios, including source scanning, genuine CLI/regex contracts, structured configuration, and guidance-delivery limits. Use existing focused resolver, guidance, and publication tests for delivery mechanics. Add or adapt executable coverage only for a concrete uncovered behavior. A packaged or resolved content inspection can verify resource inclusion, but cannot prove future agent adherence. No artificial red-green cycle is required for prose alone.

## Risks / Trade-offs

- A blanket reading could reject valid output tests -> include explicit text, pattern-matching, and authored-artifact contract examples.
- Broad "contract" claims could excuse source mirroring -> require an accepted observable requirement and a distinguishable violation, rather than declaring incidental internals contractual after implementation.
- Editing TDD headings could break dynamic assembly -> preserve manifest anchors and inspect the assembled Python skill.
- Weakening phrase checks could lose delivery coverage -> retain selection, failure/fallback, publication, and output assertions that prove the existing behavior; state what each retained check covers.
- More process could manufacture work -> allow existing evidence and non-test validation; do not add a mandatory worksheet, test count, or suite-wide cleanup.
- Prompt guidance cannot enforce adherence -> report content delivery separately from agent behavior.

## Migration Plan

Implement and review the two skill updates as one coherent checkpoint. Update the selected Python CLI governance, refine directly affected tests only where justified, and publish its generated context as the next checkpoint. Inspect packaged resources and resolved TDD content; ordinary BDD content remains independently usable without changing profile selection. Run focused tests and required project checks proportionally. No automatic machine-wide skill reinstall, release, or push is needed. Rollback reverts the resource changes and republishes the previous managed guidance through normal sync.

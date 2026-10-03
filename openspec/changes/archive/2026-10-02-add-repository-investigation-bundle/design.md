# Design

## Context

See proposal.md. Runtime traits use hooks/body/optional when; Python and utility guidance live in contexts. Profile composition, ordinary-skill resolution, the case18 adapter, and generic native hook delivery are implemented prerequisites. The builtin profile names an unconditional bootstrap reminder. Previous prototype-explore/prototype-propose resources required feasibility assessment during exploration and planning; do not carry forward an unconditional ask-first policy that conflicts with smarter-decision.

## Goals / Non-Goals

**Goals:** Author one portable investigation/feasibility procedure, expose it through a global bundle, and compose readiness-aware reminders using existing condition machinery.

**Non-Goals:** A second decision-policy engine, automatic indexing, automatic prototypes, zmem recall duplication, new OpenSpec artifacts, a new CLI checker command, or changes to skill-manifest dynamic guard syntax.

## Decisions

### Sequence and ownership

Complete the context-classification source edits and their foundation verification first. Deliver bootstrap through implement-trait-hook-delivery next. Apply this bundle after those prerequisites; source authorship alone never counts as live governance. The foundation owns armed because contexts and traits both need it; this change consumes it without a duplicate checker implementation. Compilation publication remains independently owned by implement-context-sync.

### One profile and one reminder; the skill chooses the tool

Proposed resources:

- .pspec/profiles/repository-investigation.toml: global=true, scope=user; skills=["@builtin/pspec-repo-investigation"]; traits=["@builtin/repository-investigation"].
- .pspec/skills/pspec-repo-investigation/SKILL.md: bounded evidence gathering, task-aware tool selection, and feasibility assessment, independent of OpenSpec artifact names. Use the existing caller surface for findings.
- .pspec/traits/repository-investigation.toml: sessionStart/afterCompaction, when="armed('skill', '@builtin/pspec-repo-investigation')", concise reminder to assess the task and available tools before investigating.

Do not add a separate CodeGraph-first trait or gate the generic reminder on either tool. The agent decides when it actually knows the task; hook-time selection does not know enough to choose the appropriate investigation depth. The skill checks the host's actual exposed tools and executable availability, then verifies the chosen tool can serve this repository. CLI presence is not the only supported access path: an available MCP tool can be used without assuming a local executable. Armed membership alone proves neither tool availability nor usability.

| Task and availability | Agent preference |
| --- | --- |
| Broad architecture, cross-module dependencies, or system-wide understanding; both usable | CodeGraph |
| Bounded feature, bug, symbol, or change impact; both usable | Ripwire |
| Only one usable | Use it if suitable; supplement with focused source inspection and state material coverage limits |
| Neither usable | Use ordinary search, source reading, and project evidence; do not block investigation |

For CodeGraph, check the target repository's existing .codegraph directory and available CLI/MCP interface; a marker is not proof of health. Do not index automatically. Ripwire reads a source tree, so do not invent a matching .ripwire readiness-directory requirement. Consult the installed version's help or exposed tool schema for supported operations. Tool/query failure or stale evidence leads to an honest limitation and another available route, not a claim that investigation succeeded. Do not automatically run both tools: expand or switch only when the task or remaining uncertainty justifies it. Explicit caller instructions about tool use remain authoritative.

Reference inspected on 2026-10-01: [Ripwire upstream README](https://github.com/redhat-et/ripwire). It documents task-oriented symbols, callers, and test context via CLI/MCP. The broad-versus-targeted routing here is the user's workflow policy, not a claim that one tool always has more complete coverage. Neither tool guarantees total understanding.

Alternative rejected: a tool-specific trait that always requires CodeGraph first. That removes the agent's scope/availability judgment. Separate investigation and prototype profiles are also rejected because they split the same evidence-to-uncertainty workflow.

### Resource-aware conditions use the agreed meaning of armed

Use armed(kind, exact_reference) from profile-skill-bundles: selected after exclusions, not installed or condition-true. A selected trait with false when remains armed. Ordinary Python not/and/or provides inclusion or exclusion of a contribution; it does not change bundle selection. Queries never acquire sources, invoke skills, or recursively evaluate other conditions. Unsupported queries report diagnostics rather than silently looking absent.

Other resources can query the combined profile to avoid redundant generic guidance. This change does not automatically remove existing zmem, smarter-decision, or utility guidance. Example for an alternative investigation reminder:

```toml
when = "not armed('profile', '@builtin/repository-investigation')"
```

No additional activation tables, check IDs, or command surface are needed.

### Preserve skill and authority boundaries

The investigation skill inherits any active decision policy and accepted answers from the caller; it does not require smarter-decision to be installed. It distinguishes code facts, historical decisions supplied by zmem, assumptions, and experimental observations. Use relevant current evidence before proposing a minimal experiment. Planning can describe that experiment; execution uses existing authorization. Do not manufacture an experiment, a TDD cycle, or a new document merely because the profile is present.

Alternative rejected: reviving the old unconditional prototype question. It conflicts with the configured decision level and causes irrelevant prompts in environment jobs.

## Risks / Trade-offs

- Global reminders can add noise -> keep them short, task-conditional, and excludable; procedures stay in the skill.
- Selected skill may not be installed -> armed does not claim readiness; bootstrap/installation diagnostics retain their existing contract.
- A CodeGraph directory can be stale -> qualify the marker and verify query results rather than declaring health.
- Trait conditions can observe other selected traits -> use the pre-evaluation membership snapshot, never recursively evaluate them.

## Migration Plan

Use the completed classification edits and later verified bootstrap delivery as prerequisites. Implement the shared armed binding in the foundation before authoring runtime examples as executable fixtures. Then author and validate this bundle, verify isolated composition and generic hook output, then exercise agent tool selection with both, one, neither, and failing-tool availability fixtures, and validate skill content with evidence-sufficient, uncertain planning-only, authorized experiment, and environment-only walkthroughs. Do not change the user's live installation during fixtures. Rollback can exclude the profile; it need not delete installed skills or shared callbacks.

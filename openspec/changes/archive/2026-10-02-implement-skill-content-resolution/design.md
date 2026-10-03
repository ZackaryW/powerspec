# Design

## Context

See proposal.md. The CLI scaffold exposes skill NAME --agent AGENT [--change NAME] [--json], but currently returns a non-mutating unavailable diagnostic. The reviewed .pspec/skills/pspec_tdd source and docs/examples/tdd-python-resolution.md are authored examples, not runtime evidence.

Prerequisite: establish-profile-consumer-resolution supplies catalogs, effective profile defaults, consumer discovery, and variable layers. This milestone deliberately uses disposable installed resources before bundle-resources-and-initialize adds production provisioning.

## Goals / Non-Goals

**Goals:** Make the first real read-only skill invocation produce selected content with atomic results and actionable pending questions.

**Non-Goals:** Execute a skill, interpret the conversation, install/repair/fetch resources, deliver hooks, publish config.yaml, or clear state.

## Decisions

### Explicit installed lookup and bootstrap outcomes

Use ZuAT's registry-independent `locate_skill` API for the explicit agent's installed skill. Pin revision e42dbfe64f071da145dc33d728f92ef6edd1195b and verify its public lookup API against disposable homes. Lookup takes one explicit agent and creates no ZuAT registry or observation. User/project coexistence is not a Powerspec conflict: rely on verified native selection evidence, or accept optional `--selected PATH` when the host reports the loaded installation. ZuAT validates that path against actual candidates and never substitutes another copy. An unresolved selection without host evidence is an error; Powerspec does not introduce scope ordering or a scope prompt.

Inspect support through pspec.toml without reading every branch. Installed skill without a manifest returns literal null and permits normal entrypoint use. Missing installation, unavailable executable, unreadable/broken manifest, or failed composition is an error, never null. Bootstrap itself is exempt from lookup to prevent recursion. Preserve explicit --change on answer/rerun instructions.

Default stdout is assembled Markdown, or Markdown headed # Pending choices with relevant questions, constraints, suggested answers, and where to supply answers. Pending withholds procedural content. --json represents the same outcome: null, status pending with questions, or status resolved with a content string equal to default Markdown. `--selected PATH` is lookup evidence rather than a scope preference and accepts either the installed directory or its SKILL.md. Success/pending/null exit 0; failures exit nonzero with stderr diagnostics and no success output. Progress stays on stderr.

This keeps command reads separate from installation and avoids presenting suggestions as confirmed choices.

### Manifest parsing, input evaluation, and materialization are separate

Version 1 identifies entry = SKILL.md, typed inputs/parsers, optional equality-map when guards (all conditions must match), ordered hint groups, and dynamic additions only. Validate declarations, references, types, versions, and dependency cycles first. Input dependencies arise from guards, paths, and rendered selected content. Resolve controlling inputs first; known false guards exclude branches without requesting remaining inputs.

Consumer-configuration owns variable precedence. Apply skill value defaults last. Valid effective values skip their prompts and hints; invalid values fail rather than falling back. Input default is a value; prompt default is a suggestion. Repeated hint IDs form local authored-order groups; scalar default_hint selects a group and its first matching typed read-only detector suggests a value. No hint writes state or answers for the user. Unrelated installed skills never participate.

### The shared document owns order

Keep shared flow in SKILL.md; pspec.toml declares only dynamic entries:

```toml
[[dynamic]]
section = "Red: observe the missing behavior"
pos = "after"
path = "languages/<language>.md"
source_section = "red"
```

section selects a unique exact destination heading; source_section selects a source heading or omission selects the complete file. Exclude frontmatter from entrypoint procedure; preserve it as metadata. Ignore fenced headings when finding sections. A section includes descendants until the next heading of equal or higher rank, or document end. before precedes the destination heading; after follows the full section. Preserve source headings and label inserted content concisely.

No numbered insert, old after key, inline markers, or duplicated static sequence. Missing/ambiguous active selectors are errors, not full-file or append fallbacks.

### Replacements are planned against the original document

replace substitutes the entire target heading/body/descendants. Process active replace/combine entries per target in declaration order using an empty accumulator. Replace resets content and duplicate history; combine appends distinct canonical source contributions currently retained. First combine excludes original target content. Last active replacement wins, including A/B/A. Mixed replace A, combine B, replace C, combine D yields C then D.

Active ancestor replacement groups suppress all descendant-targeted placements regardless of order or position, including child after-placements sharing an ancestor endpoint. Inactive ancestors do not suppress children. Same-target before/after surrounds the final replacement. Do not re-anchor child edits inside inserted content.

For before/after, retain first occurrence of an identical canonical destination/position/file/source-section contribution. Explicit attachment to different destinations remains distinct. This uses stable original coordinates and avoids order-dependent re-parsing.

### Materialize only selected resources, then emit once

Substitute declared variables once in paths and content. Undeclared angle-bracket prose remains literal; undeclared path variables are errors. Canonicalize selected resources including symlinks and enforce the installed skill root boundary. Inactive files need not exist. Fully assemble before output so a late missing file/section cannot leak partial success.

TDD uses Python tooling inputs guarded by language = python. Effective build_tool, test_runner, and test_command enter Python scope/red content; selected profile defaults produce uv, pytest, uv run pytest. Other language fixtures must not request Python tooling. No BDD selection is added.

### CLI readiness evolves per command

The cli-scaffold delta preserves alias/help/syntax/no-side-effect guarantees for scaffold paths, but allows a capability to replace its own placeholder. Only skill becomes functional here. Init and hook remain unavailable until their changes; sync is implemented separately by implement-context-sync and flush remains deferred. Update tests that previously expected every valid skill invocation to fail as a placeholder, while preserving remaining placeholder tests.

## Risks / Trade-offs

- Native lookup semantics may differ across agents → verify the adapter's selected identity, not a guessed scope ordering.
- Complex overlapping Markdown sections → test table-driven boundary cases and atomic failures against the original document.
- A simulation could be mistaken for completion → require real CLI output from an isolated installed skill and compare the reviewed example.

## Migration Plan

Implement manifest/input/composition layers, then installed lookup and CLI rendering. Existing bootstrap/profile source work is retained; its authored status does not count as runtime verification. Demonstrate unsupported, pending, answered, invalid, and configured Python paths through both aliases. Snapshot fixtures to prove lookup writes nothing. No real user installation or migration is performed.

Packaging/init can start after this milestone; automatic hook discovery is still delivered separately.

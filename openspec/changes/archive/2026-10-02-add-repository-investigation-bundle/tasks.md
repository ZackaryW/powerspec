# Tasks

Prerequisites, in order: establish-profile-consumer-resolution (including the reviewed context migration and armed checker), implement-skill-content-resolution, bundle-resources-and-initialize, then implement-trait-hook-delivery. This bundle follows verified bootstrap delivery. None of these prerequisites is claimed complete merely because source resources are authored.

## 1. Author the combined procedure and profile

- [x] 1.1 Create pspec-repo-investigation/SKILL.md with evidence gathering, agent-owned CodeGraph/Ripwire selection, material feasibility assessment, bounded experiments, and return-to-caller behavior; validate skill metadata and review evidence-sufficient, planning-only, already-authorized experiment, environment-only, and prior-answer walkthroughs without requiring new artifacts or repeated permission.
- [x] 1.2 Create the global user-scoped repository-investigation profile referencing the skill and one runtime reminder trait; verify real composition includes it once, excludes its exclusive contributions when requested, preserves shared resources, and does not add it to Python-specific contexts or activate TDD/BDD.

## 2. Author and verify runtime guidance

- [x] 2.1 Create the repository-investigation trait with sessionStart/afterCompaction and an armed skill guard; verify selected-skill and standalone-trait-without-skill cases through the shared condition adapter, including selection versus installation and no skill execution; the hook returns the reminder without selecting or running an investigation tool. Document that the reminder follows the caller's active decision policy.
- [x] 2.2 Validate the skill's tool-selection guidance with both-tools broad and targeted tasks, each tool alone, neither tool, MCP-only access, stale/failed queries, and expanding task scope. Check installed help/tool schemas for any concrete invocation examples. Document agent choice and fallback without adding a tool-first trait, auto-installation, automatic CodeGraph indexing, a Ripwire index-marker prerequisite, or claims of complete coverage.
- [x] 2.3 Verify the reminder uses generic existing callback registrations and preserve bootstrap/zmem/smarter-decision contributions; exercise exclusion and post-compaction dispatch with disposable consumers and document runtime selection without reinstall or native asset removal.

## 3. Integrated bundle verification

- [x] 3.1 Resolve the investigation skill and deliver the bundle through the established isolated bootstrap/hook harness; verify content delivery separately from agent execution, unchanged config.yaml, and absence of unrelated workflow prompts for an environment-only session.
- [x] 3.2 Run affected tests with uv run pytest, skill validation, and openspec validate add-repository-investigation-bundle --strict; record verified prerequisites and remaining host limitations without claiming live user installation.

## Verification evidence

- `uv run pytest -q`: 241 passed and one existing opt-in acceptance test skipped.
- The skill-creator `quick_validate.py` accepted `pspec-repo-investigation`, and strict OpenSpec validation passed.
- Focused composition and dispatch fixtures verified global deduplication, exact exclusion, standalone-trait omission through `armed`, preserved bootstrap and smarter-decision guidance, startup and compaction delivery, no TDD/BDD questions, and unchanged `config.yaml`.
- A disposable Codex home and Git consumer completed init, installed the user-scoped skill, returned ordinary-skill `null` from `pspec skill`, and delivered the reminder through both generic callbacks. No live user installation was modified.
- The implementation checkout exposed a CodeGraph executable but no `.codegraph/` index, so it was not queried or indexed. No Ripwire executable was exposed. The skill therefore relies on current CLI help or MCP schemas when those interfaces are actually available and does not publish speculative commands.

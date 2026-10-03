# Repository investigation bundle

`repository-investigation` is a global, user-scoped profile containing the
ordinary `pspec-repo-investigation` skill and one runtime reminder trait. It is
mounted once through normal profile composition and can be removed from a
consumer with:

```toml
exclude_profiles = ["@builtin/repository-investigation"]
```

Exclusion changes the effective bundle. It does not uninstall the skill or
remove the generic native hook registration.

The reminder contributes only at `sessionStart` and `afterCompaction`, and only
while `armed('skill', '@builtin/pspec-repo-investigation')` sees the skill in the
effective selection after exclusions. `armed` does not prove that the skill is
installed or executed. Hook delivery does not select an investigation tool or
start an investigation, prototype, utility plan, TDD, or BDD workflow.

The skill chooses an evidence route when it knows the task. CodeGraph is the
preferred route for broad architecture and cross-module questions when an
existing `.codegraph/` index and a usable CLI or MCP interface are present.
Ripwire is preferred for targeted symbols and localized impact when its CLI or
MCP interface can read the repository; no synthetic `.ripwire` marker is
required. One usable tool may be supplemented with direct evidence. If neither
is usable, ordinary search and source inspection remain valid.

Neither an index marker nor a successful query proves current or complete
coverage. The agent checks material findings against source, tests,
configuration, or another current observation and reports failures or stale
evidence honestly. Powerspec neither installs these tools nor creates a
CodeGraph index.

Feasibility experiments are proportional to unresolved material uncertainty.
Evidence-complete work needs no experiment. Planning records a minimal
experiment for later execution; already-authorized implementation may run that
experiment without asking for the same permission again. Findings stay in the
caller's existing conversation or artifact and follow the active decision
policy and accepted answers.

The repository used for this implementation exposed a CodeGraph CLI but had no
`.codegraph/` directory, so the implementation did not query or index it.
Ripwire exposed no local executable. The skill therefore avoids pinned Ripwire
command examples and directs agents to current CLI help or MCP schemas when an
interface is available.

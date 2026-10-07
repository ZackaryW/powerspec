# Context synchronization

Run `pspec sync` or `powerspec sync` without arguments from a configured repository. Powerspec finds the nearest owning `openspec/.pspec/config.toml` inside the current Git boundary and reconciles selected compile-time contexts into that consumer's existing `openspec/config.yaml`.

Compilation uses shared persistent `[vars]` from `config.toml`, then selected-profile defaults, global-profile defaults, and context declaration defaults. Invalid explicit values fail. `current.toml`, `_change` tables, runtime prompts, traits, and skill procedures do not participate. A malformed `current.toml` therefore does not block sync.

Declared `<variable>` placeholders and selected `<skill:name>` references are replaced once. Other angle-bracket prose remains literal. Skill references use catalog names only; sync does not inspect or execute installed skills. Attachment `when` expressions use the trusted Python condition adapter with `vars`, `armed`, `which`, `run_json`, and the invocation Git root. Their results are a publication-time snapshot. Mutable readiness belongs in runtime traits and changes only after another sync.

Eligible explicit skill references are classified using the selected catalog resources. A valid `pspec.toml` requires dynamic resolution, including an input-only manifest or inactive additions. An absent manifest means ordinary native use. Broken, unreadable, escaping, or invalid manifests fail publication; classification does not evaluate inputs or read branch content. Unmentioned skills, false attachments, bare prose, and tokens introduced by variable substitution do not produce annotations.

Each contribution with dynamic references receives a heading in first-mention order, with duplicate names removed. For example, `Use <skill:b>, <skill:a>, and <skill:b>.` produces this managed text when both manifests are valid:

```markdown
### Skills requiring dynamic resolution: b, a

When the guidance below calls for these skills, select each through your native skill integration. Before following its procedure, run `pspec resolve skill --path "<selected-skill-location>" --agent <current-agent>` from the task directory. Include `--change <name>` only for an explicitly active change. Follow returned content or pending-choice instructions; report errors without bypassing resolution.

Use b, a, and b.
```

This preamble lives inside the existing managed context/rule/operation contribution. It adds no YAML key or global skill inventory, preserves provenance and authored text, and does not activate a workflow. Repeat sync is byte-idempotent; removing a reference or manifest removes its stale heading. Known conflicting classifications for one declared name fail instead of choosing a native installation.

Supported destinations are `context`, `rules.<artifact>`, and `operations.<operation>.guidance`. Context guidance is owned through `<!-- pspec:contexts:start -->` and `<!-- pspec:contexts:end -->`. Managed list entries contain `<!-- pspec:managed -->` and a trailing caret identifier derived from the qualified context, destination, and explicit attachment ID or destination-local ordinal. Powerspec replaces only these marked contributions and preserves handwritten entries, schema selection, comments, and unrelated fields.

The command reports `updated: <path>` after atomically replacing the complete validated candidate or `unchanged: <path>` when no bytes need changing. Missing consumers, target YAML, catalog resources, invalid conditions, malformed ownership markers, and publication failures return a nonzero error without a success message. Sync does not initialize OpenSpec, refresh existing sources, install or remove skills, deliver hooks, execute plans/tests, or flush runtime state.

Sync prepares selected remote resources through the shared `powerspec` Saucepan application. It initializes the store/application when needed, acquires missing recipes, and reuses existing materializations without refreshing them. Acquisition failures leave config.yaml unchanged; successful earlier acquisitions remain available for retry. Run `pspec init --agent <agent>` to provision skills and hooks, or `pspec upgrade --agent <agent>` for explicit refresh and installation reconciliation.

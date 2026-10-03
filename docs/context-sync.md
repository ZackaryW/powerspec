# Context synchronization

Run `pspec sync` or `powerspec sync` without arguments from a configured repository. Powerspec finds the nearest owning `openspec/.pspec/config.toml` inside the current Git boundary and reconciles selected compile-time contexts into that consumer's existing `openspec/config.yaml`.

Compilation uses shared persistent `[vars]` from `config.toml`, then selected-profile defaults, global-profile defaults, and context declaration defaults. Invalid explicit values fail. `current.toml`, `_change` tables, runtime prompts, traits, and skill procedures do not participate. A malformed `current.toml` therefore does not block sync.

Declared `<variable>` placeholders and selected `<skill:name>` references are replaced once. Other angle-bracket prose remains literal. Skill references use catalog names only; sync does not inspect or execute installed skills. Attachment `when` expressions use the trusted Python condition adapter with `vars`, `armed`, `which`, `run_json`, and the invocation Git root. Their results are a publication-time snapshot. Mutable readiness belongs in runtime traits and changes only after another sync.

Supported destinations are `context`, `rules.<artifact>`, and `operations.<operation>.guidance`. Context guidance is owned through `<!-- pspec:contexts:start -->` and `<!-- pspec:contexts:end -->`. Managed list entries contain `<!-- pspec:managed -->` and a trailing caret identifier derived from the qualified context, destination, and explicit attachment ID or destination-local ordinal. Powerspec replaces only these marked contributions and preserves handwritten entries, schema selection, comments, and unrelated fields.

The command reports `updated: <path>` after atomically replacing the complete validated candidate or `unchanged: <path>` when no bytes need changing. Missing consumers, target YAML, catalog resources, invalid conditions, malformed ownership markers, and publication failures return a nonzero error without a success message. Sync does not initialize OpenSpec, fetch or refresh sources, install or remove skills, deliver hooks, execute plans/tests, or flush runtime state.

Remote profile resources must already be materialized through their registered Saucepan source identities. Sync reuses existing materializations without refreshing them and diagnoses an unavailable selected source instead of silently omitting it. Use `pspec upgrade --agent <agent>` for explicit refresh and installation reconciliation.

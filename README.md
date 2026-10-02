# Powerspec

Profile-driven project guidance and skill resolution. Powerspec composes profile
bundles, provisions skills through ZuAT, resolves dynamic skill content, and
publishes compile-time contexts into OpenSpec.

## Development

Use Python 3.12 or newer with uv:

```console
uv sync
uv run pspec --help
uv run pytest
```

`powerspec` is an alias for `pspec`. Either name without arguments shows help.
Each command also supports `--help`.

| Command | Current behavior |
| --- | --- |
| `pspec init --agent AGENT [--profile PROFILE]` | Initialize Git-root configuration and provision selected skills |
| `pspec skill NAME --agent AGENT [--change CHANGE] [--json]` | Resolve an installed skill's selected content |
| `pspec hook EVENT` | Placeholder for runtime hook guidance |
| `pspec sync` | Reconcile OpenSpec configuration |
| `pspec flush [--change CHANGE]` | Placeholder for clearing temporary variables |
| `pspec upgrade` | Placeholder for explicit remote resource upgrades |

Implemented commands report configuration and operation failures with exit **1**.
Help exits **0**; invalid syntax exits **2**. Placeholder commands emit an explicit
not-implemented diagnostic and perform no domain work. Skill lookup returns
`null` only for an installed skill without a Powerspec manifest.

See [initialization](docs/initialization.md), [skill resolution](docs/skill-resolution.md),
and [context sync](docs/context-sync.md). Remote source integration, hook delivery,
and temporary-state cleanup remain active implementation work. In particular,
missing selected remote resources are diagnosed until source integration lands.

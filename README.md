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
| `pspec init --agent AGENT [--profile PROFILE]` | Initialize Git-root configuration and provision selected skills and supported user hooks |
| `pspec skill NAME --agent AGENT [--change CHANGE] [--json]` | Resolve an installed skill's selected content |
| `pspec hook EVENT --agent AGENT [--change CHANGE]` | Resolve runtime traits from a native hook payload on stdin |
| `pspec sync` | Reconcile OpenSpec configuration |
| `pspec flush [--change CHANGE]` | Placeholder for clearing temporary variables |
| `pspec upgrade --agent <agent>` | Refresh selected remote skills and remove confirmed obsolete managed copies through recoverable ZuAT operations |

Implemented commands report configuration and operation failures with exit **1**.
Help exits **0**; invalid syntax exits **2**. Placeholder commands emit an explicit
not-implemented diagnostic and perform no domain work. Skill lookup returns
`null` only for an installed skill without a Powerspec manifest.

See [initialization](docs/initialization.md), [skill resolution](docs/skill-resolution.md),
[context sync](docs/context-sync.md), [runtime hook delivery](docs/hook-delivery.md),
[remote sources](docs/remote-sources.md), and the
[repository investigation bundle](docs/repository-investigation.md).
Temporary-state cleanup remains active implementation work.

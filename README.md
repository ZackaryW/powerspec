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
| `pspec init [--profile PROFILE]` | Establish the Git-root OpenSpec consumer and Powerspec configuration without agent installation |
| `pspec status [--json]` | Inspect the effective profile, resources, and existing source availability without mutation |
| `pspec doctor [--json]` | Check the consumer boundary and required tools without repair |
| `pspec install --agent AGENT` | Acquire missing selected sources and reconcile skills and the user-level hook dispatcher |
| `pspec resolve skill NAME --agent AGENT [--change CHANGE] [--json]` | Resolve an installed skill's selected content |
| `pspec resolve hook EVENT --agent AGENT [--change CHANGE]` | Resolve runtime traits from a native hook payload on stdin |
| `pspec sync` | Reconcile OpenSpec configuration |
| `pspec state show [--json]` | Inspect temporal global and change-scoped values |
| `pspec state clear [--change CHANGE]` | Clear all temporal values or one change-specific layer |
| `pspec config show [--json]` | Inspect committed consumer configuration |
| `pspec config profile [PROFILE]` | Set the selected profile or clear it to global-only mode |
| `pspec config edit` | Open committed configuration through `VISUAL` or `EDITOR` |
| `pspec upgrade --agent <agent>` | Refresh selected remote skills and remove confirmed obsolete managed copies through recoverable ZuAT operations |
| `pspec workset add NAME --path PATH [--json]` | Create a Git source workset or append a repository by recreating its saved definition; repeated members are unchanged |
| `pspec workset launch NAME --branch BRANCH [--change CHANGE] [--json]` | Spawn implementation worktrees, register branch-specific stores, optionally move a change, and publish an OpenSpec workset |

Implemented commands report configuration and operation failures with exit **1**.
Help exits **0**; invalid syntax exits **2**. Skill lookup returns
`null` only for an installed skill without a Powerspec manifest.
The historical `skill`, `hook`, and `flush` forms remain hidden compatibility
aliases while integrations migrate to `resolve` and `state`.

See [initialization](docs/initialization.md), [skill resolution](docs/skill-resolution.md),
[context sync](docs/context-sync.md), [runtime hook delivery](docs/hook-delivery.md),
[remote sources](docs/remote-sources.md), [temporary state](docs/temporary-state.md), and the
[repository investigation bundle](docs/repository-investigation.md).
See [worksets](docs/worksets.md) for indexed branch overrides, store routing, change transfer and recovery.

# Powerspec

Profile-driven project guidance and skill resolution. The current executable is
a Typer CLI scaffold; domain operations are not implemented yet.

## Development

Use Python 3.12 or newer with uv:

```console
uv sync
uv run pspec --help
uv run pytest
```

`powerspec` is an alias for `pspec`. Either name without arguments shows help.
Each command also supports `--help`.

| Command | Intended operation |
| --- | --- |
| `pspec init [--agent AGENT]` | Initialize project configuration and provision selected resources |
| `pspec skill NAME --agent AGENT [--change CHANGE] [--json]` | Resolve an installed skill's selected content |
| `pspec hook EVENT` | Resolve guidance for a hook event |
| `pspec sync` | Reconcile OpenSpec configuration |
| `pspec flush [--change CHANGE]` | Clear temporary runtime variables |

These commands currently emit a **not implemented** diagnostic to stderr and
exit **1**. They produce no stdout result and do not read configuration, install
resources, or change files. In particular, `skill --json` does not return `null`
or a success payload. Help exits **0**; invalid syntax exits **2**.

Command modules live in `src/powerspec/cli/`. Each handler can be implemented
independently. The next skill-bootstrap change will implement skill resolution,
initialization, and hooks; `sync` and `flush` require separate implementation.

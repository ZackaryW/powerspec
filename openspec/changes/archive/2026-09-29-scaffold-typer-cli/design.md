## Context

See proposal.md for motivation. The current package has a greeting-only `powerspec.main`, a `powerspec` console script, Python >=3.12, and the uv_build backend. There are no tests or runtime dependencies. The larger skill-bootstrap change requires a real command boundary but has not been implemented.

## Goals / Non-Goals

**Goals:** Create small replaceable command modules under `src/powerspec/cli/`, preserve the existing entrypoint, and make unfinished operations unmistakable through help and process status.

**Non-Goals:** Implement any domain operation, inspect agent installations, read consumer configuration, provision hooks, select runtime values, or change packaging to Hatchling. The separate skill-bootstrap change owns those features.

## Decisions

### Application and modules

Use Typer with explicit registration in `cli/app.py`, exported through `cli/__init__.py`. Put each handler in its own module (`init.py`, `skill.py`, `hook.py`, `sync.py`, `flush.py`) and share only a small placeholder error helper. This keeps the next implementations independent without adding service abstractions or a plugin registry. Retain `powerspec.main` as a thin delegate; both console scripts point to the CLI entrypoint. Importing the package or CLI must not run the application.

### Command boundary

Root invocation without arguments prints help successfully, as does `--help`. Each subcommand exposes help and labels its operation as a placeholder. The selected initial surface is:

| Command | Arguments/options |
| --- | --- |
| init | optional `--agent TEXT` |
| skill | required `NAME`, required `--agent TEXT`, optional `--change TEXT`, boolean `--json` |
| hook | required `EVENT` |
| sync | none beyond help |
| flush | optional `--change TEXT` |

Use ordinary Typer parsing: syntax errors exit 2. Valid placeholder invocations call a shared helper that emits a named not-implemented diagnostic on stderr and exits 1 with empty stdout, including `skill --json`. Returning null was rejected because bootstrap interprets it as successful unsupported-skill fallback. Do not read state or guess an agent. Additional adapter flags and source commands can be added with their implementation contracts.

### Dependencies and validation

Add Typer as a runtime dependency and pytest as a development dependency using uv, retaining uv_build. Commit-compatible development files include a lockfile and ignore rules for the virtual environment, Python caches, test caches, and build artifacts. Do not ignore all OpenSpec resources. Use the reviewed TDD skill directly while the resolver is unavailable: focused failing behavioral tests, then handlers, then verification with `uv run pytest`.

Use Typer's public `CliRunner` for help, syntax, output channels, exit codes, and preservation of existing fixture files; verify real `pspec` and `powerspec` executables in subprocesses as well. Exercise module imports independently to ensure they are silent. No native agent or actual user-home provisioning is required. Reference: https://typer.tiangolo.com/tutorial/testing/.

## Risks / Trade-offs

- **Placeholder mistaken for resolution** → Never emit null, resolved content, JSON success, or successful operation status.
- **Premature CLI surface** → Limit parameters to settled shapes; keep domain behavior and native transport out of handlers.
- **Alias drift** → Both installed scripts target one callable and are exercised through real subprocesses.

## Migration Plan

Land this prerequisite before `establish-skill-bootstrap-resolution`. That change will implement existing `skill`, `init`, and `hook` handlers instead of creating another CLI. `sync` and `flush` remain honest placeholders until their own implementation work. Rollback restores the prior package entrypoint; no user data migration is involved.

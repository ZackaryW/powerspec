## Why

Powerspec currently exposes only a greeting. Establish a discoverable, testable CLI boundary before implementing skill resolution, hooks, or provisioning so later features can fill command handlers without pretending unfinished operations work.

## What Changes

- Introduce a Typer application under `src/powerspec/cli/` with separate command modules and a shared placeholder diagnostic.
- Expose `pspec` and retain `powerspec` as equivalent entrypoints; keep `powerspec.main` delegating to the application.
- Provide root and command help for `init`, `skill`, `hook`, `sync`, and `flush`. Accept the already agreed skill arguments (`name`, required `--agent`, optional `--change`, `--json`), hook event, and optional change selector for flush. Reserve an optional agent selector on init without implementing discovery.
- Make valid placeholder invocations exit 1 with a diagnostic on stderr and no stdout result. Invalid syntax exits 2; help exits 0. No invocation performs project discovery, writes state, or installs anything.
- Add focused CLI tests and usage documentation, preserving `uv run pytest` and the current build backend.

## Capabilities

### New Capabilities

- `cli-scaffold`: Command discovery, argument parsing, equivalent entrypoints, and honest non-mutating placeholder behavior.

### Modified Capabilities

None. There are no established main specs. This is a prerequisite to `establish-skill-bootstrap-resolution`, whose handlers will replace the relevant placeholders.

## Impact

Changes affect Python CLI modules, package scripts/dependencies, development test setup, and README documentation. The package currently has no tests or dependencies. Typer is the runtime dependency and pytest the development test dependency. This change does not implement resolution, source acquisition, configuration synchronization, flush cleanup, initialization, hook dispatch, skill installation, or the planned Hatchling resource packaging.

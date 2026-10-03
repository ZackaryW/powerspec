# Initialize a consumer

Run from anywhere inside the target Git repository:

```console
pspec init --agent codex --profile @builtin/python-simple-cli
```

`--agent` must name one supported agent (`codex`, `claude`, `kimi`, or `pi`). A
new consumer can use `--profile`; an existing consumer reads its selection from
`openspec/.pspec/config.toml`. Omitting the profile (or configuring `profile = ""`)
selects only global profiles, after exclusions. Thus `pspec init --agent codex`
is a valid global-only bootstrap. Supplying a different profile does not overwrite
that choice: edit the configuration explicitly to change it.

Initialization plans the selected resources first, then invokes an installed
OpenSpec CLI (1.13.2 or later) with `--tools none`. It establishes the Git-root
`openspec` structure, including worktree roots, without generating repository
agent skills. Existing OpenSpec configuration, source resources, variables, and
native skills are preserved. A selected project-scoped profile can separately
install its skills into the repository through ZuAT.

For Codex and Claude, initialization also provisions the generic Powerspec
runtime dispatcher into the agent's user-level hook settings through ZuAT. Hook
scope is independent from profile skill scope. Kimi and Pi currently report an
unsupported runtime-delivery surface because no context-capable mapping has been
verified. See [runtime hook delivery](hook-delivery.md).

The consumer's `.gitignore` covers `current.toml`, while `config.toml` remains
trackable. A tracked current file is reported; initialization does not untrack it.
Existing shared `[vars]` and change-specific `[_change.<name>]` values remain in
place. Repeating initialization reuses matching managed installations.

The command reports each skill's source, profile, agent, scope, and outcome, plus
the hook dispatcher outcome.
Successful actions remain available after a partial failure. Resolve the stated
conflicts and rerun the command. It never forces replacement of unmanaged or
edited copies. See [skill installation](skill-installation.md).

Initialization establishes skill availability and supported native hook
registrations. It does not publish contexts into `config.yaml`, execute skills,
or prove an agent followed delivered guidance. Run `pspec sync` to publish
configured contexts.

The bundled zmem and ADHD-friendly profiles reference external Saucepan sources.
If their registered materializations are unavailable, initialization reports the
missing selected resources. A bundled-only trial can explicitly exclude those
profiles in the consumer configuration:

```toml
profile = "@builtin/python-simple-cli"
exclude-profiles = ["@builtin/zmem-lifecycle", "@builtin/adhd-friendly"]

[vars]
utility_path = "src/example/utils"
```

Exclusion changes this consumer's selection; it never removes skills shared with
other consumers. Examples and integration tests use disposable agent homes and
ZuAT registries. `ZUAT_HOME` redirects ZuAT's registry for isolated checks.

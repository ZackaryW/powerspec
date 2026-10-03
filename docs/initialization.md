# Initialize a consumer

Run inside the target Git repository:

```console
pspec init --profile @builtin/python-simple-cli --agent codex
pspec sync
```

Initialization creates the Git-root OpenSpec/Powerspec consumer, acquires missing
selected sources, and provisions selected skills and hooks for the supplied
agent. There is no separate install command. Repeat `init --agent codex` to
prepare another machine or reconcile that agent after changing profile selection.

`--profile` sets a new consumer's selection; later runs reuse config.toml.
An omitted or empty profile selects global profiles after exclusions. Conflicting
profile options are rejected: edit config.toml to change an existing choice.

Plain `pspec init` prepares the consumer and selected sources without guessing an
agent or provisioning assets. Rerun with `--agent` for agent setup. Unsupported
agents are rejected before consumer writes.

OpenSpec CLI 1.13.2 or later is required when bootstrapping OpenSpec. Powerspec
invokes it with `--tools none`; ZuAT installs skills at each profile's declared
scope. Bundled OpenSpec skills use user scope. Only project-scoped profiles create
repository-local agent skills. Generic hooks use the agent's user-level settings.
Unsupported hook surfaces are reported explicitly; see [hook delivery](hook-delivery.md).

Existing config.yaml, config.toml, current.toml, and unrelated native assets are
preserved. A tracked current.toml is reported; initialization adds its ignore rule
but does not untrack it. Later failures leave established consumer files and
successful assets in place. Resolve the error and rerun init with the same options;
matching materializations and assets are reused.

`pspec sync` publishes contexts, acquiring missing sources without refreshing
existing revisions or installing skills/hooks. `pspec upgrade --agent codex`
refreshes selected sources and reconciles installations, committing obsolete
managed removals only after successful preparation.

The bundled zmem and ADHD-friendly profiles use external Git recipes. First use
of init or sync lazily prepares the shared Powerspec Saucepan application.
Native secret and index initialization are delegated to Saucepan; existing
store data is never deleted or rekeyed to bypass failure. A missing credential
service or damaged existing store remains an error. Do not copy an encrypted
Saucepan store between computers as a substitute for initialization.

For a bundled-only consumer, explicitly exclude the external profiles:

```toml
profile = "@builtin/python-simple-cli"
exclude-profiles = ["@builtin/zmem-lifecycle", "@builtin/adhd-friendly"]

[vars]
utility_path = "src/example/utils"
```

Excluding a profile does not uninstall skills shared by other projects.
Initialization does not execute skills or prove that an agent followed guidance.

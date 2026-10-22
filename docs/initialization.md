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

## Follow progress

Init and upgrade report the active stage on stderr as work happens: consumer
setup, Saucepan manager preparation, each source, each skill check, hooks and
saving selections. Source-only init reports its source work too. For example:

```text
Starting: Preparing source: zmem (main)
Starting: Materializing source: zmem
Waiting: Materializing source: zmem (5s elapsed; no completion reported)
done: Materializing source: zmem (8.2s)
Starting: Checking skill 1/22: i-have-adhd
failed: Checking skill 1/22: i-have-adhd (0.1s): native target is unowned
```

A waiting line appears every five seconds while a stage is blocked. It means
PowerSpec is still waiting; it does not prove that a transfer is advancing.
Failures retain their original diagnostics and retry guidance. A heartbeat does
not extend timeouts or retry a mutation. Progress stops when the operation exits
or is interrupted.

Progress remains readable when redirected. In PowerShell, capture it separately
with `pspec init --agent codex 2> init-progress.log`. Final results remain on
stdout, including the existing per-item summary. Hook/skill resolution and doctor
JSON do not acquire lifecycle progress output.

## Setup and recovery

OpenSpec CLI 1.14.3 or later is required when bootstrapping OpenSpec. Powerspec
invokes it with `--tools none`; ZuAT installs skills at each profile's declared
scope. Bundled OpenSpec skills use user scope. Only project-scoped profiles create
repository-local agent skills. Generic hooks use the agent's user-level settings.
Unsupported hook surfaces are reported explicitly; see [hook delivery](hook-delivery.md).

Existing config.yaml, config.toml, current.toml, and unrelated native assets are
preserved. A tracked current.toml is reported; initialization adds its ignore rule
but does not untrack it. Later failures leave established consumer files and
successful assets in place. Resolve the error and rerun init with the same options;
matching materializations and assets are reused.

`pspec sync` publishes contexts using existing retained source selections without
fetching or installing skills/hooks. Run `pspec init` first for missing sources. `pspec upgrade --agent codex`
refreshes selected sources and reconciles installations, committing obsolete
managed removals only after successful preparation.

The bundled zmem and ADHD-friendly profiles use external Git recipes. First use
of init lazily registers the Powerspec application and a separate consumer scope.
Basic integrity is the default; credentials and keyring integrity remain opt-in.
Existing incompatible or damaged stores are rejected, never deleted or rekeyed.
See [remote sources](remote-sources.md) for retained bindings and recovery.

For a bundled-only consumer, explicitly exclude the external profiles:

```toml
profile = "@builtin/python-simple-cli"
exclude-profiles = ["@builtin/zmem-lifecycle", "@builtin/adhd-friendly"]

[vars]
utility_path = "src/example/utils"
```

Excluding a profile does not uninstall skills shared by other projects.
Initialization does not execute skills or prove that an agent followed guidance.

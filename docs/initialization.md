# Initialize a consumer

Run from anywhere inside the target Git repository:

```console
pspec init --profile @builtin/python-simple-cli
pspec sync
pspec install --agent codex
```

A new consumer can use `--profile`; an existing consumer reads its selection from
`openspec/.pspec/config.toml`. Omitting the profile (or configuring `profile = ""`)
selects only global profiles, after exclusions. Thus `pspec init`
is a valid global-only bootstrap. Supplying a different profile does not overwrite
that choice: edit the configuration explicitly to change it.

Initialization invokes an installed
OpenSpec CLI (1.13.2 or later) with `--tools none`. It establishes the Git-root
`openspec` structure, including worktree roots, without generating repository
agent skills. Existing OpenSpec configuration, variables, and native skills are
preserved. Initialization neither opens Saucepan nor invokes ZuAT.

`pspec install --agent <agent>` acquires missing configured sources, provisions
selected skills, and reconciles the generic Powerspec runtime dispatcher into
the agent's user-level hook settings through ZuAT. Hook scope is independent
from profile skill scope. Kimi and Pi currently report an
unsupported runtime-delivery surface because no context-capable mapping has been
verified. See [runtime hook delivery](hook-delivery.md).

The consumer's `.gitignore` covers `current.toml`, while `config.toml` remains
trackable. A tracked current file is reported; initialization does not untrack it.
Existing shared `[vars]` and change-specific `[_change.<name>]` values remain in
place. Repeating initialization preserves matching consumer files. Installation
reports each skill and hook outcome; successful assets remain available after a
partial failure. Resolve conflicts and rerun install. See
[skill installation](skill-installation.md).

Initialization does not publish contexts, acquire sources, install skills,
register hooks, execute skills, or prove an agent followed guidance. Run
`pspec sync` to publish configured contexts and `pspec install --agent <agent>`
to install agent assets.

The bundled zmem and ADHD-friendly profiles declare external Git recipes.
Installation lazily establishes the single `powerspec` Saucepan application and
acquires any selected recipe that has no current materialization. Existing
materializations are reused without refresh. Acquisition or provisioning
failures are reported as incomplete installation. A bundled-only trial can
explicitly exclude those profiles in the consumer configuration:

```toml
profile = "@builtin/python-simple-cli"
exclude-profiles = ["@builtin/zmem-lifecycle", "@builtin/adhd-friendly"]

[vars]
utility_path = "src/example/utils"
```

Exclusion changes this consumer's selection; it never removes skills shared with
other consumers. Examples and integration tests use disposable agent homes and
ZuAT registries. `ZUAT_HOME` redirects ZuAT's registry for isolated checks.

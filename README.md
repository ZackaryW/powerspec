<div align="center">

# Powerspec

**Reusable project guidance for OpenSpec and coding agents.**

[Getting started](#quick-start) · [How it works](#how-powerspec-works) · [Commands](#commands) · [Documentation](#documentation)

</div>

Powerspec gives a repository a reusable operating model. Profiles select the
contexts, runtime traits, and agent skills that belong to a kind of project.
Powerspec installs those skills through ZuAT, publishes compact guidance into
OpenSpec, and resolves detailed instructions only when an agent needs them.

Its working principles are:

```text
→ reusable profiles instead of copied instructions
→ compact OpenSpec context instead of permanent prompt bulk
→ explicit runtime resolution instead of guessed state
→ persistent project choices separated from temporary change state
→ user-level skills shared across repositories
```

Powerspec is an OpenSpec companion. OpenSpec owns specifications, changes, and
workflow operations; Powerspec supplies the project-specific guidance and skill
content used while carrying out those operations.

## See it in action

```text
$ pspec init --profile @builtin/python-simple-cli --agent codex
installed: OpenSpec and Powerspec skills at Codex user scope
installed: Powerspec hook dispatcher
initialized: this Git repository

$ pspec sync
updated: openspec/config.yaml

$ pspec status
profile: @builtin/python-simple-cli
contexts, traits, skills, and sources are resolved from one effective bundle
```

The repository now carries committed project configuration under
`openspec/.pspec/config.toml`. Codex receives the selected skills in its
user-level skill directory, while `openspec/config.yaml` receives only the
guidance that should remain visible during OpenSpec operations.

<details>
<summary><strong>What does a consumer configuration look like?</strong></summary>

```toml
profile = "@builtin/python-simple-cli"

# Optional global profiles can be disabled for this repository.
exclude-profiles = ["@builtin/adhd-friendly"]

[vars]
language = "python"
build_tool = "uv"
test_runner = "pytest"
test_command = "uv run pytest"

# Persistent values can also belong to one OpenSpec change.
[_change.add-export-command]
utility_path = "src/example/utils"
```

Temporary choices use the same shape in the gitignored
`openspec/.pspec/current.toml`. Archiving a change can clear only its temporary
layer while preserving committed configuration.

</details>

## Why use Powerspec?

- **Apply one project model consistently.** A profile can bundle shared
  contexts, runtime traits, subprofiles, and skills for a Python CLI, a
  repository investigation workflow, or another reusable setup.
- **Keep agent context focused.** Compile-time contexts place concise guidance
  in OpenSpec. A skill's `pspec.toml` can select language or framework sections
  when the skill is invoked.
- **Share skills without copying them into every repository.** User-scoped
  profiles install skills once for the chosen agent. Project-scoped profiles
  remain available when isolation is required.
- **Preserve explicit state.** Committed configuration, temporary session
  choices, and change-specific values have defined precedence and lifetimes.
- **Coordinate multi-repository implementation.** Worksets can turn an OpenSpec
  repository list into isolated Git worktrees, branch-specific stores, and an
  implementation workset.

## Quick Start

Powerspec requires Python 3.12 or newer, Git, and
[OpenSpec](https://github.com/Fission-AI/OpenSpec) 1.13.2 or newer. Install
Powerspec directly from its Git repository with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install "git+https://github.com/ZackaryW/powerspec.git"
```

Then run Powerspec inside an existing Git repository:

```bash
cd your-project
pspec init --profile @builtin/python-simple-cli --agent codex
pspec sync
pspec status
```

`--profile` selects the repository's initial profile. Later runs preserve the
selection in `openspec/.pspec/config.toml`. Omit the profile to use global
profiles only.

`--agent` is the provisioning boundary. `pspec init --agent codex` installs the
selected skills and generic hook dispatcher at their declared scopes. Bare
`pspec init` creates the consumer and prepares sources without choosing an agent
or installing agent assets. There is no separate Powerspec install command.

To inspect the setup without changing it:

```bash
pspec doctor
pspec status
pspec config show
```

## How Powerspec works

Powerspec resolves the nearest `openspec/.pspec/config.toml` inside the current
Git boundary and composes four resource types:

| Resource | Responsibility | Evaluation time |
| --- | --- | --- |
| **Profile** | Bundles other profiles, contexts, traits, skills, defaults, sources, and one skill installation scope | Bundle composition |
| **Context** | Publishes stable project guidance into `openspec/config.yaml` | `pspec sync` |
| **Trait** | Returns guidance for native agent callbacks when its condition matches | `pspec resolve hook` |
| **Skill** | Supplies a complete agent procedure, optionally resolved through a skill-local `pspec.toml` | Skill invocation |

The builtin global profile supplies the OpenSpec workflow skills and the
Powerspec bootstrap skill. These are bundled from a pinned OpenSpec source when
Powerspec is built and installed to the selected agent's user scope during
`pspec init --agent <agent>`.

Profiles can also declare Git sources. Saucepan owns their materialization;
ZuAT owns installation into native agent locations. `pspec sync` acquires a
missing selected source but preserves its current revision. `pspec upgrade`
refreshes selected sources and reconciles managed skill installations.

## Commands

| Command | Purpose |
| --- | --- |
| `pspec init [--profile PROFILE] [--agent AGENT]` | Create or reuse the Git-root consumer, ensure sources, and optionally provision one agent |
| `pspec sync` | Reconcile selected compile-time contexts into `openspec/config.yaml` |
| `pspec status [--json]` | Show the effective profile bundle and source availability without mutation |
| `pspec doctor [--json]` | Check the consumer boundary and required tools without repairing them |
| `pspec config show\|profile\|edit` | Inspect or update committed consumer configuration |
| `pspec state show\|clear` | Inspect or clear temporary global or change-specific values |
| `pspec resolve skill NAME --agent AGENT` | Return the applicable content for an installed skill |
| `pspec resolve hook EVENT --agent AGENT` | Resolve runtime trait guidance for a native callback |
| `pspec upgrade --agent AGENT` | Refresh selected remote sources and reconcile managed agent assets |
| `pspec workset add NAME --path PATH` | Add a Git repository to an OpenSpec source workset |
| `pspec workset launch NAME --branch BRANCH` | Create implementation worktrees, stores, and an output OpenSpec workset |

`powerspec` is an alias for `pspec`. Run `pspec <command> --help` for complete
arguments, indexed workset overrides, JSON output options, and exit behavior.

## Documentation

**Start here:** [Initialize a consumer](docs/initialization.md), then read
[Context synchronization](docs/context-sync.md) and
[Skill installation](docs/skill-installation.md).

→ **[Resolution foundation](docs/foundation.md)**: profiles, variables, conditions, and bundle composition<br>
→ **[Skill resolution](docs/skill-resolution.md)**: dynamic skill inputs and selected content<br>
→ **[Runtime hooks](docs/hook-delivery.md)**: trait delivery through native callbacks<br>
→ **[Remote sources](docs/remote-sources.md)**: Saucepan identities, acquisition, and upgrades<br>
→ **[Temporary state](docs/temporary-state.md)**: shared and change-specific runtime choices<br>
→ **[Repository investigation](docs/repository-investigation.md)**: CodeGraph and Ripwire selection<br>
→ **[Worksets](docs/worksets.md)**: multi-repository worktrees, stores, and change transfer<br>
→ **[Packaged resources](docs/packaged-resources.md)**: pinned OpenSpec skills and Hatch builds

## Development

Clone the repository and use uv to create the development environment:

```bash
git clone https://github.com/ZackaryW/powerspec.git
cd powerspec
uv sync
uv run pspec --help
uv run pytest
```

Changes to behavior are planned under `openspec/changes/` and folded into the
main specifications when archived. The project uses its own profiles, contexts,
traits, and skills from `.pspec/` to govern development.

## License

[MIT](LICENSE)

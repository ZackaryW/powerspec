# Spec Delta

## MODIFIED Requirements

### Requirement: Agent protocols live under resolve

`pspec resolve skill --path <selected-location> --agent <agent>` SHALL consume a supplied skill directory, SKILL.md or pspec.toml, resolving relative paths from the process working directory without changing consumer discovery; --agent SHALL be invocation context only. It SHALL keep Markdown by default, optional JSON, null for ordinary skills and optional --change. Pending responses SHALL give a rerun command keeping the full path, agent and change, and JSON responses SHALL add skill_path.

#### Scenario: Resolve supported skill content
- **WHEN** an agent supplies the selected location of a configured skill through resolve skill --path
- **THEN** Powerspec emits that skill's resolved document in the requested representation without searching native installations

#### Scenario: Dispatch a native hook
- **WHEN** an installed Codex or Claude callback invokes resolve hook with an event and agent from a consumer working directory
- **THEN** Powerspec resolves the nearest owning consumer from that directory and emits applicable hook guidance without consuming a native payload

#### Scenario: Dispatch an Antigravity hook
- **WHEN** an installed Antigravity callback invokes resolve hook with the explicit payload-workspace option from the host's fixed hooks directory
- **THEN** Powerspec resolves the nearest owning consumer of each payload workspace path and emits applicable hook guidance in Antigravity's envelope

#### Scenario: Stdin stays open
- **WHEN** hook resolution runs without the payload-workspace option and with an open stdin pipe whose writer sends no bytes and does not close it
- **THEN** the command completes its resolution without waiting for input or end-of-file

#### Scenario: Payload cannot redirect consumer discovery
- **WHEN** a caller supplies stdin containing another repository's cwd, malformed JSON, or arbitrary text, and the payload-workspace option is not given
- **THEN** the command ignores that input and resolves only from its process working directory

#### Scenario: Direct command without a payload
- **WHEN** the user runs a supported hook resolution command with stdin closed or unavailable
- **THEN** the command uses its arguments and working directory without reporting a missing or invalid native payload

#### Scenario: Unsupported selector
- **WHEN** the caller supplies an unsupported logical event or native hook agent mapping
- **THEN** the command reports the error on stderr and exits nonzero without reading stdin or emitting successful guidance

#### Scenario: Former name-only invocation
- **WHEN** the caller runs pspec resolve skill pspec-tdd --agent codex
- **THEN** the command reports migration to --path and directs the caller to obtain the path through native skill integration without inspecting installed copies

#### Scenario: Former selected option
- **WHEN** the caller uses the previous positional-name and --selected syntax
- **THEN** the command reports that --path now carries the selected location without executing a compatibility lookup

#### Scenario: Directory and file forms
- **WHEN** the caller supplies a skill directory, its SKILL.md, or its pspec.toml using --path
- **THEN** all three forms resolve against the same skill root and preserve task-directory consumer selection

#### Scenario: Path with spaces remains usable on retry
- **WHEN** a pending invocation supplies a path containing spaces and an explicit change
- **THEN** the rerun preserves a correctly quoted path and the same agent and change, and JSON identifies the canonical skill directory

#### Scenario: Missing path is not discovery
- **WHEN** a caller omits both --path and --ref even though same-named skills are installed
- **THEN** the invocation fails without enumerating installations or selecting a default copy

#### Scenario: Console aliases agree
- **WHEN** identical explicit-path requests are made through pspec and powerspec
- **THEN** their stdout, stderr, and exit behavior agree

#### Scenario: Catalog selection is explicit
- **WHEN** the caller supplies --ref helper instead of --path
- **THEN** the command uses only selected Powerspec catalog resources and does not interpret the name as an installed skill or a filesystem path

#### Scenario: Conflicting selectors
- **WHEN** the caller supplies both --path and --ref
- **THEN** the command fails before resolving either target and emits no successful payload

#### Scenario: JSON responses keep their fields
- **WHEN** a skill resolves or is pending with --json
- **THEN** the response keeps its status, skill, agent, change and content or questions fields, adds skill_path, and takes the skill name from the selected SKILL.md

### Requirement: Hook resolution reads only its arguments

`pspec resolve hook <event> --agent <agent>` SHALL take its logical event and agent from arguments, discover the nearest owning consumer from its working directory, and use optional --change as the only change selector. It SHALL NOT read, parse, poll or wait for stdin, even when a host supplies a payload, unless the explicit --stdin-workspace option is given, which permits only the bounded workspace read defined for the selected agent. Results SHALL go to stdout in the agent's native additional-context envelope, with diagnostics on stderr and documented nonzero exits; no contribution SHALL produce no stdout.

#### Scenario: No contribution writes nothing
- **WHEN** no trait contributes guidance for the event
- **THEN** hook resolution writes nothing to stdout

#### Scenario: Change selector for hook inputs
- **WHEN** hook resolution needs change-scoped inputs
- **THEN** only an explicit --change argument selects that change

#### Scenario: Default invocation never touches stdin
- **WHEN** hook resolution runs for any agent without --stdin-workspace
- **THEN** it does not read, parse, or poll stdin

#### Scenario: Payload option is the only stdin exception
- **WHEN** hook resolution runs with --stdin-workspace for an agent that supports it
- **THEN** it reads stdin only to obtain the workspace and takes no event, variable, answer, or change from it

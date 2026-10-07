# Spec Delta

## MODIFIED Requirements

### Requirement: Agent protocols live under resolve

`pspec resolve skill --path <selected-location> --agent <agent>` SHALL consume an explicitly supplied skill directory, SKILL.md, or pspec.toml. Relative locations SHALL be interpreted against the task's process working directory; supplying a path SHALL NOT change the directory used for consumer discovery. The agent option SHALL identify invocation context rather than drive native installation lookup. Skill resolution SHALL preserve Markdown-by-default, optional JSON, literal null for an explicitly supplied ordinary skill, and optional --change inputs. Pending responses SHALL provide a rerun command retaining the complete selected path, agent, and explicit change. JSON pending and resolved responses SHALL identify the canonical skill directory through a skill_path field while retaining their existing status, skill, agent, change, and content/questions fields; the skill name SHALL come from the selected SKILL.md's declared name.

The previous positional-name form, including the old --selected option, SHALL fail with a nonzero diagnostic explaining the new --path invocation and native-selection responsibility. It SHALL NOT perform legacy name discovery, infer a path from a bare name, or silently treat a positional name as a relative path. Missing --path or --agent SHALL be an invalid invocation. Failed invocations SHALL emit no successful payload. Both pspec and powerspec console scripts SHALL expose the same contract.

`pspec resolve hook <event> --agent <agent>` SHALL select its logical event and supported agent from command arguments and discover the nearest owning consumer from its process working directory. Optional --change SHALL remain the only selector for change-scoped hook inputs. Hook resolution SHALL NOT read, parse, poll, or wait for standard input, including when a native host supplies a payload. Protocol success SHALL write results to stdout; diagnostics SHALL use stderr and documented nonzero exit codes. Hook guidance SHALL retain the supported agent's native additional-context response envelope and an absent contribution SHALL produce no stdout.

#### Scenario: Resolve supported skill content
- **WHEN** an agent supplies the selected location of a configured skill through resolve skill --path
- **THEN** Powerspec emits that skill's resolved document in the requested representation without searching native installations

#### Scenario: Dispatch a native hook
- **WHEN** an installed agent callback invokes resolve hook with an event and agent from a consumer working directory
- **THEN** Powerspec resolves the nearest owning consumer from that directory and emits applicable hook guidance without consuming a native payload

#### Scenario: Stdin stays open
- **WHEN** hook resolution runs with an open stdin pipe whose writer sends no bytes and does not close it
- **THEN** the command completes its resolution without waiting for input or end-of-file

#### Scenario: Payload cannot redirect consumer discovery
- **WHEN** a caller supplies stdin containing another repository's cwd, malformed JSON, or arbitrary text
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
- **WHEN** a caller omits --path even though same-named skills are installed
- **THEN** the invocation fails without enumerating installations or selecting a default copy

#### Scenario: Console aliases agree
- **WHEN** identical explicit-path requests are made through pspec and powerspec
- **THEN** their stdout, stderr, and exit behavior agree

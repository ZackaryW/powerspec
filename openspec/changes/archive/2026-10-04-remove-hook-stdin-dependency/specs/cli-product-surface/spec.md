# Spec Delta

## MODIFIED Requirements

### Requirement: Agent protocols live under resolve

`pspec resolve skill <name> --agent <agent>` SHALL preserve the existing Markdown-by-default and optional JSON skill protocol, including optional change-scoped inputs. `pspec resolve hook <event> --agent <agent>` SHALL select its logical event and supported agent from command arguments and discover the nearest owning consumer from its process working directory. Optional `--change` SHALL remain the only selector for change-scoped hook inputs. Hook resolution SHALL NOT read, parse, poll, or wait for standard input, including when a native host supplies a payload. Protocol success SHALL write results to stdout; diagnostics SHALL use stderr and documented nonzero exit codes. Hook guidance SHALL retain the supported agent's native additional-context response envelope and an absent contribution SHALL produce no stdout.

#### Scenario: Resolve supported skill content
- **WHEN** an agent requests a configured skill through `resolve skill`
- **THEN** Powerspec emits the resolved skill document in the requested representation

#### Scenario: Dispatch a native hook
- **WHEN** an installed agent callback invokes `resolve hook` with an event and agent from a consumer working directory
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
- **WHEN** the caller supplies an unsupported logical event or agent mapping
- **THEN** the command reports the error on stderr and exits nonzero without reading stdin or emitting successful guidance

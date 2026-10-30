# Spec Delta

## Purpose

Define how Powerspec delivers trait guidance to Google Antigravity through its native SessionStart hook, including the response envelope, registration shape, workspace discovery from the hook payload, multi-project sessions, and which boundaries Antigravity cannot support.

## ADDED Requirements

### Requirement: Antigravity maps sessionStart to its native SessionStart
Powerspec SHALL map the logical sessionStart event for the antigravity agent to Antigravity's native SessionStart callback. It SHALL report afterCompaction for antigravity as having no verified context-delivery mapping, and SHALL NOT register any other Antigravity lifecycle callback.

#### Scenario: Resolve sessionStart guidance
- **WHEN** `pspec resolve hook sessionStart --agent antigravity` runs in a configured consumer
- **THEN** it returns the applicable sessionStart guidance

#### Scenario: Compaction is reported unsupported
- **WHEN** `pspec resolve hook afterCompaction --agent antigravity` runs
- **THEN** it exits nonzero on stderr with the no-verified-mapping diagnostic and writes nothing to stdout

#### Scenario: Trait selects both logical events
- **WHEN** a trait selects sessionStart and afterCompaction and the agent is antigravity
- **THEN** its guidance is delivered at session start only and no compaction restoration is claimed

#### Scenario: High-frequency callbacks are never registered
- **WHEN** hooks are provisioned for antigravity
- **THEN** no PreInvocation, PostInvocation, PreToolUse, PostToolUse, or Stop callback is registered

### Requirement: Antigravity guidance uses the injected system message envelope
For antigravity, Powerspec SHALL emit eligible guidance on stdout as one JSON object whose `injectSteps` contains a single `systemMessage` step carrying the guidance text. It SHALL NOT use the Codex or Claude `hookSpecificOutput` envelope. When there is no guidance, stdout SHALL be empty, as for other agents.

#### Scenario: Guidance is delivered
- **WHEN** a sessionStart dispatch for antigravity has eligible guidance
- **THEN** stdout parses as JSON with `injectSteps[0].systemMessage.systemMessage` equal to the guidance and no `hookSpecificOutput` key

#### Scenario: Guidance with multiple traits
- **WHEN** several traits contribute guidance
- **THEN** their bodies appear in one message in the same order and separation as for other agents

#### Scenario: No contribution
- **WHEN** the workspace has no owning consumer, no matching trait, or only false conditions
- **THEN** stdout is empty and the exit status is zero

### Requirement: Antigravity registration is a keyed flat SessionStart entry
Provisioning for antigravity SHALL install one hook named `powerspec` in the user-level Antigravity hooks document through ZuAT. Its SessionStart value SHALL be a flat list holding one command handler that runs `pspec resolve hook sessionStart --agent antigravity --stdin-workspace` with an explicit timeout of at most five seconds and no fields Antigravity does not document.

#### Scenario: First installation
- **WHEN** `pspec init --agent antigravity` provisions hooks and no `powerspec` entry exists
- **THEN** the hooks document gains exactly that entry, ZuAT records ownership, and other named hooks are unchanged

#### Scenario: Repeated provisioning
- **WHEN** provisioning runs again with the entry current and owned
- **THEN** it reports the hook reused and writes nothing

#### Scenario: Foreign occupant
- **WHEN** a `powerspec` entry exists without ZuAT ownership and differs from the desired entry
- **THEN** provisioning fails with ZuAT's diagnostic and the document is unchanged

#### Scenario: Handler uses only documented fields
- **WHEN** the registration is generated
- **THEN** its handler contains only `type`, `command`, and `timeout`, and the command contains no quotes or backslashes

### Requirement: Payload workspace discovery is explicit and opt-in
`pspec resolve hook` SHALL read the hook payload from stdin only when `--stdin-workspace` is given, and only for an agent whose mapping declares payload workspaces. It SHALL use the payload's `workspacePaths` as the directories for consumer discovery and condition evaluation, and SHALL take no event, variable, answer, or change value from the payload.

#### Scenario: Workspace from payload
- **WHEN** the process runs from `~/.gemini/config` and the payload names `workspacePaths: ["/work/app"]` that has a consumer
- **THEN** guidance is selected from the consumer owning `/work/app`

#### Scenario: Launch from a subdirectory
- **WHEN** the payload's only workspace path is a subdirectory of a consumer
- **THEN** the nearest owning consumer above it is used, as for a nested working directory

#### Scenario: Option on an unsupported agent
- **WHEN** `--stdin-workspace` is given with `--agent codex` or `--agent claude`
- **THEN** the command exits nonzero with a diagnostic before reading stdin

#### Scenario: Other payload fields are ignored
- **WHEN** the payload also carries `lastUserInput`, `modelName`, or another cwd-like field
- **THEN** none of them influences event selection, variables, or consumer discovery

### Requirement: Multi-project sessions delegate project choice to the agent
When the payload lists more than one workspace path, Powerspec SHALL resolve each path's owning consumer, count each consumer once, and deliver one message holding a section per consumer with guidance, each headed by that project's directory name and path. The message SHALL first tell the agent to follow only the section for the project it is actively implementing or updating changes in.

#### Scenario: Workset with two consumer repositories
- **WHEN** the payload lists the worktrees `api-feature-x` and `web-feature-x`, each a consumer with guidance
- **THEN** one message carries the selection instruction, then a section headed for `api-feature-x` and one for `web-feature-x`, each with only its own consumer's guidance

#### Scenario: Two paths in one consumer
- **WHEN** two listed paths resolve to the same consumer
- **THEN** that consumer's guidance appears once

#### Scenario: Only one listed project has guidance
- **WHEN** several paths are listed and only one consumer contributes guidance
- **THEN** its guidance is still delivered under its project heading with the selection instruction, so it is not applied to the other projects

#### Scenario: Single workspace path
- **WHEN** the payload lists exactly one workspace path
- **THEN** the guidance is delivered without project headings or the selection instruction, identical to a single-project session

#### Scenario: No listed project has guidance
- **WHEN** no listed path has a consumer contributing guidance
- **THEN** stdout is empty and the exit status is zero

### Requirement: One failing project does not suppress the others
In a multi-project session, a configuration or authored-resource error in one consumer SHALL omit only that consumer's section and be reported on stderr naming its path; other consumers' guidance SHALL still be delivered. If every consumer that was found fails, the command SHALL exit nonzero with no stdout.

#### Scenario: One malformed consumer
- **WHEN** one of two listed consumers has a malformed configuration
- **THEN** stderr names that consumer, stdout carries the other consumer's section with the selection instruction, and the exit status is zero

#### Scenario: Every consumer fails
- **WHEN** every listed consumer has a malformed configuration
- **THEN** stdout is empty and the exit status is nonzero

### Requirement: Payload read is bounded and never waits for end of input
With `--stdin-workspace`, the command SHALL stop reading as soon as one complete JSON object has arrived or a 0.5 second budget has elapsed, whichever is first, and SHALL NOT wait for end-of-file. An interactive terminal stdin SHALL NOT be read; the command SHALL use its working directory instead.

#### Scenario: Stdin left open after the payload
- **WHEN** the host writes a complete payload and keeps the pipe open
- **THEN** the command resolves using that payload and exits without waiting for the pipe to close

#### Scenario: Stdin open with no bytes
- **WHEN** the host keeps the pipe open and sends nothing
- **THEN** the command gives up within the budget and completes within the native five-second limit

#### Scenario: Direct interactive invocation
- **WHEN** a user runs the command with the option in a terminal inside a consumer
- **THEN** it resolves from the working directory without blocking on input

### Requirement: Unusable payload yields no guidance without failing the session
If stdin is not an interactive terminal and its payload is empty, times out, is not a JSON object, or lists no workspace path naming an existing directory, the command SHALL write a diagnostic to stderr, deliver no guidance, and exit zero with empty stdout. It SHALL NOT fall back to the process working directory in that case.

#### Scenario: Malformed payload
- **WHEN** stdin contains text that is not a JSON object
- **THEN** stderr names the unusable payload, stdout is empty, and the exit status is zero

#### Scenario: Missing workspace directory
- **WHEN** a listed workspace path does not exist
- **THEN** that path contributes nothing, stderr names it, and any other listed path is still resolved

#### Scenario: Working directory is not a fallback
- **WHEN** the payload is unusable but the process runs inside a consumer
- **THEN** no guidance is delivered from that consumer

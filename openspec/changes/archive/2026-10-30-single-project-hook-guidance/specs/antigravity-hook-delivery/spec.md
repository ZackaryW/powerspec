## ADDED Requirements

### Requirement: Multi-project sessions deliver one project's guidance
When the payload's existing workspace paths resolve to two or more distinct consumers, Powerspec SHALL NOT combine their guidance. The message SHALL list each consumer once by name and path, tell the agent to follow only guidance for the project it is actively working in, and give the command that returns one project's guidance from that project's folder. Only a selected workset default's guidance SHALL be included.

#### Scenario: Workset with two consumer repositories and no default
- **WHEN** the payload lists the worktrees `api-feature-x` and `web-feature-x`, each a consumer with guidance, and no workset default matches
- **THEN** one message lists both projects with their paths and the per-project command, and contains neither project's guidance

#### Scenario: Agent fetches another project's guidance
- **WHEN** the agent runs the listed command from `web-feature-x`
- **THEN** it receives only `web-feature-x`'s guidance

#### Scenario: Paths resolving to one consumer
- **WHEN** several listed paths resolve to the same consumer, or only one listed path has a consumer
- **THEN** that consumer's guidance is delivered without a project list or heading, identical to a single-project session

#### Scenario: Single workspace path
- **WHEN** the payload lists exactly one workspace path
- **THEN** the guidance is delivered without project headings or the project list, identical to a single-project session

#### Scenario: No listed path has a consumer
- **WHEN** no listed path has a consumer
- **THEN** stdout is empty and the exit status is zero

#### Scenario: Large workset stays small
- **WHEN** a seven-consumer workset with no default is opened, each consumer having about 6,000 characters of guidance
- **THEN** the delivered message contains none of that guidance and stays far below the observed delivery limit

### Requirement: Failing projects in multi-project sessions
In a multi-project session, a consumer whose configuration cannot be discovered SHALL be reported on stderr naming its path and left out of the project list; the others SHALL still be listed. If every consumer that was found fails, the command SHALL exit nonzero with no stdout.

#### Scenario: One malformed consumer
- **WHEN** one of three listed consumers has a malformed configuration
- **THEN** stderr names that consumer, stdout lists the other two, and the exit status is zero

#### Scenario: Every consumer fails
- **WHEN** every listed consumer has a malformed configuration
- **THEN** stdout is empty and the exit status is nonzero

## REMOVED Requirements

### Requirement: Multi-project sessions delegate project choice to the agent
**Reason**: Combining every consumer's guidance applied rules to projects the agent was not working in and approached Antigravity's delivery size limit; work targets one project at a time.
**Migration**: Set a workset default with `pspec workset default` to receive that project's guidance at session start; for any other project, run `pspec resolve hook sessionStart --agent antigravity` from its folder.

### Requirement: One failing project does not suppress the others
**Reason**: Replaced by "Failing projects in multi-project sessions", since non-default projects no longer contribute guidance sections.
**Migration**: None; a malformed consumer is still named on stderr without suppressing the rest of the message.

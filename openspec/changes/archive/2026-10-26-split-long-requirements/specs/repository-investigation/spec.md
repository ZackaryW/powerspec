## MODIFIED Requirements

### Requirement: The agent chooses investigation tools by task and availability

The investigation skill SHALL instruct the agent to assess the current task and actual tool availability before selecting an investigation route. With both tools usable, it SHALL prefer CodeGraph for broad, architectural and cross-module understanding, and Ripwire for targeted changes, symbol investigation and localized impact. This SHALL be agent judgment within the accepted task, not fixed by profile mounting or hook dispatch. Explicit caller tool constraints SHALL remain authoritative.

#### Scenario: Both tools support broad investigation
- **WHEN** both tools are usable and the task needs system-wide understanding
- **THEN** the skill directs the agent to prefer CodeGraph, verify findings against relevant evidence, and avoid claiming exhaustive coverage

#### Scenario: Both tools support a targeted change
- **WHEN** both tools are usable and the task is a bounded change or symbol investigation
- **THEN** the skill directs the agent to prefer Ripwire without first requiring a CodeGraph query

#### Scenario: Caller constrains the tools
- **WHEN** the caller explicitly restricts which investigation tools may be used
- **THEN** that constraint governs over the skill's default preference

#### Scenario: The task expands
- **WHEN** targeted investigation reveals a material system-wide dependency question
- **THEN** the agent can broaden its investigation and switch to CodeGraph when usable, without making dual-tool execution mandatory

#### Scenario: Only one tool is usable
- **WHEN** only CodeGraph or only Ripwire can serve the repository
- **THEN** the skill directs the agent to assess its fit, use it where useful, and supplement missing evidence without demanding the absent tool

#### Scenario: Neither tool is usable
- **WHEN** neither tool can serve the repository
- **THEN** generic investigation remains available through ordinary search and source inspection without automatic installation or indexing

#### Scenario: MCP access without a local executable
- **WHEN** a tool has an available repository-usable MCP interface but no local CLI executable
- **THEN** the skill recognizes the usable interface instead of declaring the tool unavailable solely from executable discovery

#### Scenario: Stale index or failed query
- **WHEN** the selected tool fails or supplies stale/incomplete evidence
- **THEN** the agent reports material limitations and uses another available route, without asserting successful or complete understanding

### Requirement: Investigation leads to bounded feasibility assessment

The skill SHALL establish the requested question, inspect relevant current evidence and boundaries, separate observed facts from assumptions, and identify remaining material feasibility uncertainty, reusing accepted answers under the active decision policy. Evidence that resolves feasibility SHALL be recorded without manufacturing an experiment; otherwise the skill SHALL define the smallest useful experiment with its question, scope, observable evidence and dependent work.

#### Scenario: Existing evidence settles feasibility
- **WHEN** current evidence answers the relevant feasibility question
- **THEN** the skill explains that conclusion and returns to the caller without demanding a prototype

#### Scenario: Planning exposes material uncertainty
- **WHEN** a planning-only task needs experimental evidence before dependent implementation
- **THEN** the skill describes a bounded experiment and identifies dependent work without implementing it or blocking independent investigation

#### Scenario: Experiment is already authorized
- **WHEN** the current request already authorizes the bounded experiment
- **THEN** the skill uses that authorization, reports actual observations and limitations, and does not ask for the same permission again

#### Scenario: No mandatory prototype document
- **WHEN** the skill defines or runs a bounded experiment
- **THEN** it requires neither a standalone prototype document nor repeated approval

#### Scenario: Environment-only task has no feasibility question
- **WHEN** environment maintenance or a simple edit supplies no material feasibility uncertainty
- **THEN** the reminder does not force a prototype, utility plan, TDD, or BDD cycle

## ADDED Requirements

### Requirement: Investigation tool availability reflects usable interfaces

Availability SHALL reflect exposed CLI or MCP interfaces and repository usability, not armed membership alone. CodeGraph SHALL require the target repository's existing index marker and a usable access path; the marker SHALL NOT establish index health or coverage. Ripwire SHALL NOT require an analogous pre-existing index directory. With one usable tool the agent SHALL use it when suitable and supplement with source evidence; with neither, it SHALL use ordinary search and source inspection.

#### Scenario: CodeGraph index marker is absent
- **WHEN** the target repository has no existing CodeGraph index marker
- **THEN** CodeGraph is not treated as usable for that repository

#### Scenario: Ripwire without an index directory
- **WHEN** Ripwire has a usable access path but the repository has no Ripwire index directory
- **THEN** Ripwire is not treated as unavailable for that reason

### Requirement: Investigation tool selection stays bounded

Tool selection SHALL NOT itself authorize installation, automatic CodeGraph indexing, or running both tools for every task. Material failures or limitations SHALL be reported, and investigation SHALL continue through available routes without invented success.

#### Scenario: No automatic tool setup
- **WHEN** a preferred tool is missing or its repository is not indexed
- **THEN** the agent does not install the tool or create an index as part of selecting a route

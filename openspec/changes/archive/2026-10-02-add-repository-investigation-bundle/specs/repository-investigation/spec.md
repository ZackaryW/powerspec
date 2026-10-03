## Purpose

Provide one reusable global bundle that investigates repository evidence and assesses material feasibility uncertainty before dependent work.

## ADDED Requirements

### Requirement: Investigation and feasibility share one global bundle

The repository-investigation profile SHALL be global, use user skill-installation scope, and contribute a bounded investigation/feasibility skill plus runtime guidance. It SHALL remain subject to normal profile exclusions. Mounting, installing, or delivering the bundle SHALL NOT itself run the skill, create a prototype, or activate a testing workflow. The skill SHALL be usable outside OpenSpec and SHALL keep reporting in the caller's existing conversation or artifact.

#### Scenario: Global selection and exclusion
- **WHEN** a consumer selects a profile without excluding repository-investigation
- **THEN** the effective bundle includes the investigation resources once
- **WHEN** the consumer excludes repository-investigation and no other selected profile references its resources
- **THEN** those resources contribute no guidance, without uninstalling skills or generic hooks

### Requirement: Runtime reminders respect selected resources

The primary investigation reminder SHALL target sessionStart and afterCompaction and use the shared armed capability to require its investigation skill in the effective bundle. It SHALL direct use only when repository evidence or feasibility uncertainty matters to the current task. It SHALL preserve existing decision policy, explicit answers, and task boundaries. It SHALL NOT duplicate zmem lifecycle instructions or add its own mandatory decision-mode prompt.

#### Scenario: Investigation skill is selected
- **WHEN** the reminder matches the event and its skill is armed
- **THEN** it can contribute bounded investigation guidance without claiming installation or execution

#### Scenario: Standalone trait lacks the selected skill
- **WHEN** another profile selects only the reminder trait without its investigation skill
- **THEN** its armed condition omits that reminder without acquisition or skill execution

### Requirement: The agent chooses investigation tools by task and availability

The investigation skill SHALL instruct the agent to assess the current task and actual tool availability before selecting an investigation route. With both tools usable, it SHALL prefer CodeGraph for broad system understanding, architecture, and cross-module relationships, and Ripwire for targeted changes, symbol investigation, and localized impact. This SHALL be agent judgment within the accepted task, not a fixed tool selected by profile mounting or hook dispatch. Explicit caller tool constraints SHALL remain authoritative.

Availability assessment SHALL account for exposed CLI or MCP interfaces and repository usability rather than armed resource membership alone. CodeGraph use SHALL require the target repository's existing index marker and a usable access path; the marker SHALL NOT establish index health or complete coverage. The skill SHALL NOT impose an analogous pre-existing index-directory requirement on Ripwire. With only one usable tool, the agent SHALL use it when suitable and supplement with source evidence as needed. With neither usable, it SHALL use ordinary search and source inspection. Tool selection SHALL NOT itself authorize installation, automatic CodeGraph indexing, or running both tools for every task. Material failures or limitations SHALL be reported, and investigation SHALL continue through available routes without invented success.

#### Scenario: Both tools support broad investigation
- **WHEN** both tools are usable and the task needs system-wide understanding
- **THEN** the skill directs the agent to prefer CodeGraph, verify findings against relevant evidence, and avoid claiming exhaustive coverage

#### Scenario: Both tools support a targeted change
- **WHEN** both tools are usable and the task is a bounded change or symbol investigation
- **THEN** the skill directs the agent to prefer Ripwire without first requiring a CodeGraph query

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

#### Scenario: The task expands
- **WHEN** targeted investigation reveals a material system-wide dependency question
- **THEN** the agent can broaden its investigation and switch to CodeGraph when usable, without making dual-tool execution mandatory

### Requirement: Investigation leads to bounded feasibility assessment

The skill SHALL establish the requested question, inspect relevant current evidence and boundaries, separate observed facts from assumptions, and identify remaining material feasibility uncertainty. It SHALL reuse accepted answers and follow the active decision policy. If current evidence resolves feasibility, it SHALL record the relevant conclusion without manufacturing an experiment. Otherwise it SHALL define the smallest useful experiment with its question, scope, observable success/failure evidence, and dependent work. Existing task authorization SHALL count; planning-only work SHALL record an experiment for later authorized execution rather than run it. No mandatory standalone prototype document or repeated approval SHALL be required.

#### Scenario: Existing evidence settles feasibility
- **WHEN** current evidence answers the relevant feasibility question
- **THEN** the skill explains that conclusion and returns to the caller without demanding a prototype

#### Scenario: Planning exposes material uncertainty
- **WHEN** a planning-only task needs experimental evidence before dependent implementation
- **THEN** the skill describes a bounded experiment and identifies dependent work without implementing it or blocking independent investigation

#### Scenario: Experiment is already authorized
- **WHEN** the current request already authorizes the bounded experiment
- **THEN** the skill uses that authorization, reports actual observations and limitations, and does not ask for the same permission again

#### Scenario: Environment-only task has no feasibility question
- **WHEN** environment maintenance or a simple edit supplies no material feasibility uncertainty
- **THEN** the reminder does not force a prototype, utility plan, TDD, or BDD cycle

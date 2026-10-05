# Skill Bootstrap Specification

## Purpose

Give agents one explicit pre-skill lookup convention with clear unsupported, pending, resolved, and failed outcomes and native selection preserved.

## Requirements

### Requirement: Bootstrap performs explicit skill lookup

The pspec-skill-bootstrap skill SHALL instruct the agent to run `pspec resolve skill <name> --agent <current-agent>` before following another skill's procedure. When the calling workflow has an active change, the agent SHALL also pass --change <name> and retain it on reruns; otherwise it SHALL omit the selector instead of guessing. When the host reports the exact installed copy it selected, the agent MAY pass its directory or SKILL.md through `--selected PATH`; Powerspec SHALL validate that evidence against the target agent's installed candidates. The name SHALL identify the intended skill and the agent argument SHALL identify the actual invoking agent. Missing or unsupported agent identity SHALL be diagnosed rather than guessed from shell or installation order. Bootstrap itself SHALL be exempt from its own lookup requirement. The command SHALL NOT activate or execute the requested skill.

#### Scenario: Invoke a supported skill
- **WHEN** an agent following bootstrap selects an installed TDD skill
- **THEN** it requests that skill for its own agent identity before reading the complete procedure
- **AND** it follows the resolved content rather than loading all language and framework branches

#### Scenario: Bootstrap exemption
- **WHEN** the agent reads pspec-skill-bootstrap
- **THEN** it follows the bootstrap instructions directly without recursively looking up bootstrap

#### Scenario: Explicit target is missing
- **WHEN** a lookup omits the required agent argument
- **THEN** the command reports invalid invocation without searching every agent or returning null

#### Scenario: Host reports its selected copy
- **WHEN** native rules cannot choose between installed copies and the host supplies the loaded path
- **THEN** lookup validates and resolves that exact candidate without inventing scope precedence

### Requirement: Null means unsupported rather than failed

When the requested installed skill has no Powerspec support manifest, successful lookup SHALL return the literal null result and bootstrap SHALL direct the agent to follow that skill's installed entrypoint normally. Unsupported fallback SHALL NOT require loading the full skill first. A missing installation, unresolved native identity, unreadable or malformed manifest, invalid input, or failed resolution SHALL return an actionable error with unsuccessful process status and SHALL NOT return null. Unavailable Powerspec itself SHALL be reported as unavailable, not represented as a successful unsupported lookup.

#### Scenario: Ordinary installed skill
- **WHEN** the requested skill exists for the target agent but has no pspec.toml
- **THEN** lookup succeeds with null and the agent uses its normal installed instructions

#### Scenario: Supported manifest is broken
- **WHEN** the installed skill has pspec.toml but it cannot be parsed
- **THEN** lookup reports the manifest error and bootstrap does not silently follow the unrestricted full skill

#### Scenario: Skill is not installed
- **WHEN** the named skill cannot be located for the target agent
- **THEN** lookup reports the missing installation without installing it or claiming unsupported fallback

### Requirement: Pending choices remain distinct from resolved guidance

A supported lookup SHALL identify whether it is resolved or waiting for input. A pending result SHALL identify the relevant unanswered choices, any suggested defaults, and how to supply answers and rerun the same lookup. Bootstrap SHALL have the agent obtain required answers before following dependent instructions. A suggestion, silence, or elapsed time SHALL NOT count as an answer. A resolved result SHALL supply the relevant skill content directly and SHALL NOT require the agent to retrieve every referenced file separately.

#### Scenario: Framework choice is unresolved
- **WHEN** a supported skill needs a framework choice not supplied by configuration or defaults
- **THEN** the result is pending, not null, and instructions depending on that choice are not presented as selected guidance

#### Scenario: Answers are supplied
- **WHEN** the agent reruns the lookup after an explicit answer is available
- **THEN** resolution uses that answer and returns the applicable instructions

### Requirement: Skill lookup defaults to Markdown with optional JSON

Without --json, a resolved skill lookup SHALL emit the assembled skill Markdown directly on stdout, without a JSON envelope or outer code fence. A pending lookup SHALL emit clearly labelled Markdown headed `Powerspec skill resolution pending`, with relevant questions and instructions for supplying answers and rerunning; it SHALL withhold procedural skill content. With --json, resolved output SHALL be an object with status resolved and a content string containing the same assembled Markdown; pending output SHALL be an object with status pending and questions. Both formats SHALL use the same resolution outcome and exit-status contract. Unsupported installed skills SHALL return literal null with successful status in either mode. Failures SHALL use nonzero status and stderr diagnostics without emitting a successful result; progress SHALL remain on stderr.

#### Scenario: Default resolved output
- **WHEN** a supported skill resolves without --json
- **THEN** stdout contains the selected Markdown document directly, preserving content order and concise provenance

#### Scenario: Structured resolved output
- **WHEN** the same lookup is requested with --json and unchanged inputs
- **THEN** the resolved object's content equals the Markdown returned by the default format

#### Scenario: Pending default output
- **WHEN** required skill inputs are unresolved without --json
- **THEN** stdout clearly presents `Powerspec skill resolution pending` and answer/rerun instructions rather than a skill procedure

#### Scenario: JSON option preserves unsupported fallback
- **WHEN** an installed skill without a manifest is requested with or without --json
- **THEN** lookup returns literal null with successful status in either format

### Requirement: Native agent selection owns skill precedence

The invoking agent SHALL own selection and precedence between user-level and project-level installed skills. Powerspec SHALL resolve the skill selected in that native context rather than impose profile-based copy selection, independently rank installation scopes, or request a scope decision solely because both copies exist. Optional `--selected PATH` SHALL carry host evidence only and SHALL fail when the path is not an installed candidate for that agent/name/cwd. A profile's scope SHALL determine installation destination only. This does not remove diagnostics for malformed selected content, unresolved native identity, or conflicting writes to the same installation destination.

#### Scenario: Both user and project copies exist
- **WHEN** the agent selects a skill under its native precedence rules while copies exist at both scopes
- **THEN** Powerspec resolves that selected skill without treating coexistence as an ambiguity or substituting the copy declared by a profile's install scope

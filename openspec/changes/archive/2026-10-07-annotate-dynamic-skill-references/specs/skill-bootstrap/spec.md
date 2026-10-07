# Spec Delta

## MODIFIED Requirements

### Requirement: Bootstrap performs explicit skill lookup

The pspec-skill-bootstrap skill SHALL describe a conditional handoff for an already native-selected dynamic skill rather than require a pre-skill lookup for every invocation. The agent SHALL discover and select skills through its native skill integration. Generated guidance SHALL identify mentioned manifest-backed skills that need Powerspec content assembly, and bundled dynamic entrypoints SHALL support direct native invocation. Ordinary skills SHALL NOT require a Powerspec call before the agent reads or follows them.

When dynamic assembly is needed, the agent SHALL supply the exact selected skill location to `pspec resolve skill`, retain the task working directory, and supply its actual agent identity as invocation context. An explicit active change SHALL be passed through --change and retained on reruns; absent an explicit change, the agent SHALL omit it. The command SHALL NOT discover, activate, or execute the requested skill. The bootstrap helper itself SHALL remain an ordinary skill and SHALL NOT require recursive resolution. A missing selected path SHALL be reported as a missing handoff input rather than cause Powerspec to search installations or the agent to choose a catalog source path as a substitute.

#### Scenario: Invoke a supported skill
- **WHEN** an agent's native integration selects a manifest-backed skill referenced by generated dynamic-resolution guidance
- **THEN** it supplies that selected location to Powerspec before following the procedure
- **AND** it follows the returned content rather than loading every dynamic branch

#### Scenario: Ordinary native invocation
- **WHEN** an agent selects an ordinary skill such as openspec-explore with no Powerspec manifest
- **THEN** it uses the native skill procedure without a pre-skill Powerspec command

#### Scenario: Bootstrap exemption
- **WHEN** the agent invokes pspec-skill-bootstrap to understand the targeted handoff
- **THEN** it follows the helper directly without resolving it or other ordinary skills through Powerspec

#### Scenario: Explicit target is missing
- **WHEN** the agent needs dynamic assembly but its native integration has not provided an accessible selected location
- **THEN** it reports the missing location without asking Powerspec to enumerate copies or manufacturing a precedence rule

#### Scenario: Explicit change is retained
- **WHEN** a pending dynamic invocation belongs to an explicitly supplied active change
- **THEN** the retry retains the same selected location, agent, task working directory, and change selector

#### Scenario: Host reports its selected copy
- **WHEN** the native integration supplies the selected skill location
- **THEN** Powerspec consumes that location directly without validating it against an enumerated set of installed candidates

### Requirement: Null means unsupported rather than failed

When the explicitly supplied existing skill has no Powerspec support manifest, successful resolution SHALL return literal null and the targeted handoff guidance SHALL direct the agent to follow that selected skill's ordinary native entrypoint. This fallback SHALL support direct explicit calls and catalog/native revision differences; it SHALL NOT establish a requirement to probe ordinary skills. A missing or invalid supplied location, unreadable or malformed manifest, invalid input, or failed resolution SHALL return an actionable error with unsuccessful process status and SHALL NOT return null. Unavailable Powerspec itself SHALL be reported as unavailable, not represented as a successful unsupported lookup.

#### Scenario: Ordinary installed skill
- **WHEN** a caller explicitly supplies an existing selected skill without pspec.toml
- **THEN** resolution succeeds with null and the agent follows that copy's ordinary instructions without inspecting other copies

#### Scenario: Supported manifest is broken
- **WHEN** the selected skill has pspec.toml but it cannot be parsed
- **THEN** resolution reports the manifest error and the agent does not silently follow unresolved dynamic instructions

#### Scenario: Skill is not installed
- **WHEN** the supplied skill location no longer exists
- **THEN** resolution reports that path error without searching installations, installing content, or claiming unsupported fallback

### Requirement: Pending choices remain distinct from resolved guidance

A supported resolution SHALL identify whether it is resolved or waiting for input. A pending result SHALL identify the relevant unanswered choices, any suggested defaults, the owning answer location when available, and how to supply answers and rerun the same explicit-location invocation. The agent SHALL obtain required answers before following dependent instructions. A suggestion, silence, or elapsed time SHALL NOT count as an answer. A resolved result SHALL supply the relevant skill content directly and SHALL NOT require the agent to retrieve every referenced file separately. Reruns SHALL retain the selected location and explicit invocation selectors. Resolution SHALL remain non-interactive and SHALL NOT read user answers from stdin or write them itself.

#### Scenario: Framework choice is unresolved
- **WHEN** a supported skill needs a framework choice not supplied by configuration or defaults
- **THEN** the result is pending, not null, and instructions depending on that choice are not presented as selected guidance

#### Scenario: Answers are supplied
- **WHEN** the agent reruns the same selected-location invocation after an explicit answer is available
- **THEN** resolution uses that answer and returns the applicable instructions

#### Scenario: Selected path contains spaces
- **WHEN** a pending invocation targets a skill path containing spaces
- **THEN** the displayed rerun preserves that complete path and the agent/change selectors without falling back to name-based discovery

### Requirement: Skill lookup defaults to Markdown with optional JSON

Without --json, a resolved explicit-location skill invocation SHALL emit the assembled skill Markdown directly on stdout, without a JSON envelope or outer code fence. A pending invocation SHALL emit clearly labelled Markdown headed `Powerspec skill resolution pending`, with relevant questions and instructions for supplying answers and rerunning; it SHALL withhold procedural skill content. With --json, resolved output SHALL be an object with status resolved and a content string containing the same assembled Markdown; pending output SHALL be an object with status pending and questions. Both formats SHALL use the same resolution outcome and exit-status contract. Explicitly supplied ordinary skills SHALL return literal null with successful status in either mode. Failures SHALL use nonzero status and stderr diagnostics without emitting a successful result; progress SHALL remain on stderr.

#### Scenario: Default resolved output
- **WHEN** a supported skill resolves without --json
- **THEN** stdout contains the selected Markdown document directly, preserving content order and concise provenance

#### Scenario: Structured resolved output
- **WHEN** the same explicit-location invocation is requested with --json and unchanged inputs
- **THEN** the resolved object's content equals the Markdown returned by the default format

#### Scenario: Pending default output
- **WHEN** required skill inputs are unresolved without --json
- **THEN** stdout clearly presents `Powerspec skill resolution pending` and answer/rerun instructions rather than a skill procedure

#### Scenario: JSON option preserves unsupported fallback
- **WHEN** an explicitly supplied skill without a manifest is requested with or without --json
- **THEN** resolution returns literal null with successful status in either format

### Requirement: Native agent selection owns skill precedence

The invoking agent SHALL own skill discovery and selection through its native integration, including precedence between user, project, and other native-supported locations. Powerspec SHALL consume the supplied selected location without performing a second native lookup, independently ranking scopes, checking membership in an installation registry, or asking for a scope decision solely because multiple copies exist. Profile scope SHALL determine provisioning destination only. Catalog-based dynamic annotations SHALL NOT replace native selection or supply a catalog author's path as the selected installed location. Provisioning ownership and write-conflict checks SHALL remain separate from runtime content assembly.

#### Scenario: Both user and project copies exist
- **WHEN** the agent selects one skill while copies exist at both scopes
- **THEN** Powerspec resolves the supplied location without inspecting coexistence or substituting the profile's installation target

#### Scenario: Native integration supports another location
- **WHEN** the agent supplies a valid selected skill outside Powerspec's known installation roots
- **THEN** Powerspec validates its content boundaries without rejecting it for lack of native registration

#### Scenario: Provisioning still checks ownership
- **WHEN** a separate init or upgrade operation reconciles installed skills
- **THEN** its existing ownership and conflicting-write checks still apply independently of the path-based resolution contract

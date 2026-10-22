# Skill Bootstrap Specification

## Purpose

Give agents one explicit pre-skill lookup convention with clear unsupported, pending, resolved, and failed outcomes and native selection preserved.

## Requirements

### Requirement: Bootstrap performs explicit skill lookup

The ordinary pspec-skill-bootstrap skill SHALL describe two explicit routes: catalog retrieval for a pspec:<skill> target needed by the current task, and the conditional handoff for an already native-selected dynamic skill. Its discovery description SHALL identify user pspec: requests and applicable configured scenario guidance as triggers. The user SHALL NOT have to name the skill again when its owning guidance already calls for it in the current scenario. The owning guidance SHALL retain responsibility for task conditions and permitted fallbacks; bootstrap SHALL own only the selected skill's content handoff and SHALL NOT enumerate, load, or resolve all configured skills. For ordinary native invocation the agent SHALL discover and select skills through its native skill integration, without a universal pre-skill lookup. Generated guidance SHALL identify mentioned manifest-backed skills that need Powerspec content assembly, and bundled dynamic entrypoints SHALL support direct native invocation. Ordinary native skills SHALL NOT require a Powerspec call before the agent reads or follows them. A needed pspec: target SHALL use the catalog route even when the selected catalog skill is ordinary.

When dynamic assembly is needed for native invocation, the agent SHALL supply the exact selected skill location to `pspec resolve skill`, retain the task working directory, and supply its actual agent identity as invocation context. An explicit active change SHALL be passed through --change and retained on reruns; absent an explicit change, the agent SHALL omit it. That native-path invocation SHALL NOT discover, activate, or execute the requested skill. The bootstrap helper itself SHALL remain an ordinary skill and SHALL NOT require recursive resolution. A missing selected path SHALL be reported as a missing handoff input rather than cause Powerspec to search installations or the agent to choose a catalog source path as a substitute.

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

For native invocation, the invoking agent SHALL own skill discovery and selection through its native integration, including precedence between user, project, and other native-supported locations. Powerspec SHALL consume the supplied selected location without performing a second native lookup, independently ranking scopes, checking membership in an installation registry, or asking for a scope decision solely because multiple copies exist. Profile scope SHALL determine provisioning destination only. Catalog-based dynamic annotations SHALL NOT replace native selection or supply a catalog author's path as the selected installed location. Provisioning ownership and write-conflict checks SHALL remain separate from runtime content assembly.

An explicit pspec: invocation SHALL select Powerspec catalog content through --ref independently of native copy precedence. That namespace SHALL NOT serve as a fallback for a missing native-selected path, and a missing catalog resource SHALL NOT trigger installation or substitution of a native copy.

#### Scenario: Both user and project copies exist
- **WHEN** the agent selects one skill while copies exist at both scopes
- **THEN** Powerspec resolves the supplied location without inspecting coexistence or substituting the profile's installation target

#### Scenario: Native integration supports another location
- **WHEN** the agent supplies a valid selected skill outside Powerspec's known installation roots
- **THEN** Powerspec validates its content boundaries without rejecting it for lack of native registration

#### Scenario: Provisioning still checks ownership
- **WHEN** a separate init or upgrade operation reconciles installed skills
- **THEN** its existing ownership and conflicting-write checks still apply independently of the path-based resolution contract

#### Scenario: Explicit namespace selects a different route
- **WHEN** both a catalog resource and a native-selected copy share the requested name
- **THEN** pspec: uses catalog selection while native invocation continues to use the host-selected path

### Requirement: Bootstrap routes needed Powerspec skill content

Bootstrap SHALL retrieve a needed pspec: target through --ref from the task directory, using the actual agent and explicit change only. Applicable scenario guidance SHALL suffice without another user mention. Selection alone SHALL NOT trigger retrieval. Bootstrap SHALL follow resolved content directly, preserve pending identity and confirmed answers, and report failures without substitution. Supporting resources and further procedures SHALL be retrieved only when needed.

#### Scenario: Resolve an uninstalled selected skill
- **WHEN** the user requests pspec:helper and helper is selected only through resolve-skills
- **THEN** bootstrap retrieves and follows its procedure without installing helper into a native skill directory

#### Scenario: Configured scenario selects the skill
- **WHEN** the task matches an applicable persistent or runtime rule calling for pspec:A and the user has not named A
- **THEN** bootstrap retrieves A without asking the user to repeat its name or retrieving B and C merely because they are selected

#### Scenario: Scenario rule does not apply
- **WHEN** the session can see rules for A, B, and C but the current task matches none of them
- **THEN** bootstrap retrieves none of those procedures solely because their rules or profile selections are present

#### Scenario: Another scenario becomes relevant later
- **WHEN** scenario A has used A and a later task first requires B
- **THEN** bootstrap retrieves B at that point while C remains deferred, without imposing a one-skill-per-session limit

#### Scenario: Qualify an ambiguous name
- **WHEN** the resolver reports several exact selected references for pspec:helper
- **THEN** bootstrap presents the relevant choice instead of guessing a source or selecting an installed copy

#### Scenario: Preserve pending invocation identity
- **WHEN** a catalog request with an explicit change returns pending inputs
- **THEN** bootstrap obtains the missing answers and retries with the concrete returned reference, same task directory, agent, and change

#### Scenario: Ordinary request needs no manifest
- **WHEN** pspec:helper identifies a selected ordinary skill
- **THEN** bootstrap follows the returned procedure directly rather than treating it as native-path null or requiring pspec.toml

#### Scenario: Returned dynamic content is already assembled
- **WHEN** resolved catalog content includes a shared entrypoint's native-resolution explanation
- **THEN** bootstrap follows the assembled result without resolving that same procedure recursively

#### Scenario: Invocation preserves task authority
- **WHEN** a requested skill's procedure proposes a workflow or external action
- **THEN** bootstrap preserves the user's scope and existing authorization rather than treating content retrieval as permission for additional actions

#### Scenario: Owning guidance permits unavailable-memory fallback
- **WHEN** required memory tooling is unavailable and the owning standing rule permits Git and current-source investigation
- **THEN** bootstrap preserves that work with an explicit limitation without claiming successful memory verification or loading an unrelated substitute procedure

#### Scenario: Routing invocation and discovery
- **WHEN** a user request or applicable configured rule requires pspec:<name-or-qualified-reference>
- **THEN** bootstrap removes only pspec:, supplies that selector to --ref, and searches only effective profile selections including resolve-only entries
- **AND** it retains task cwd, invoking agent and any explicit change without inferring a change
- **AND** bootstrap follows its own ordinary native entrypoint without recursive resolution

#### Scenario: Pending answers remain explicit
- **WHEN** catalog resolution returns pending questions
- **THEN** bootstrap obtains only missing required answers, preserves confirmed answers, withholds dependent work and retries with the concrete reference
- **AND** suggestions, preselection, silence and elapsed time are not treated as answers

#### Scenario: Catalog failure remains visible
- **WHEN** the consumer, selected source, command or requested target is unavailable, a name is unknown or unselected, or a manifest is invalid
- **THEN** bootstrap reports failure without installing skills, guessing paths, substituting native copies or following ordinary-content fallback
- **AND** ambiguity is presented as the returned exact-reference choice

#### Scenario: Supporting resources remain deferred
- **WHEN** resolved content refers to relative resources or later skill dependencies
- **THEN** bootstrap uses the durable source directory and reads those resources only when the active task or procedure requires them
- **AND** an explicitly permitted owning-guidance fallback is reported as limited separate work, never successful resolution, execution or memory verification

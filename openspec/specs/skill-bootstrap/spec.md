# Skill Bootstrap Specification

## Purpose

Give agents one explicit pre-skill lookup convention with clear unsupported, pending, resolved, and failed outcomes and native selection preserved.

## Requirements

### Requirement: Bootstrap performs explicit skill lookup

The pspec-skill-bootstrap skill SHALL describe two explicit routes: catalog retrieval for a pspec:<skill> target the task needs, and the conditional handoff for a native-selected dynamic skill. Its description SHALL name user pspec: requests and applicable scenario guidance as triggers, so users need not repeat a skill guidance names. Owning guidance SHALL keep conditions and fallbacks; bootstrap SHALL own only the content handoff, never enumerating, loading or resolving all configured skills.

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

When the explicitly supplied existing skill has no Powerspec manifest, successful resolution SHALL return literal null and handoff guidance SHALL direct the agent to that skill's ordinary native entrypoint, without requiring ordinary skills to be probed. A missing or invalid location, unreadable or malformed manifest, invalid input or failed resolution SHALL return an actionable error and unsuccessful status, never null. Unavailable Powerspec SHALL be reported as such, not as unsupported.

#### Scenario: Ordinary installed skill
- **WHEN** a caller explicitly supplies an existing selected skill without pspec.toml
- **THEN** resolution succeeds with null and the agent follows that copy's ordinary instructions without inspecting other copies

#### Scenario: Supported manifest is broken
- **WHEN** the selected skill has pspec.toml but it cannot be parsed
- **THEN** resolution reports the manifest error and the agent does not silently follow unresolved dynamic instructions

#### Scenario: Skill is not installed
- **WHEN** the supplied skill location no longer exists
- **THEN** resolution reports that path error without searching installations, installing content, or claiming unsupported fallback

#### Scenario: Catalog and native revisions differ
- **WHEN** the native-selected copy lacks a manifest that the catalog revision of the same skill has
- **THEN** resolution returns null for the selected copy and the agent follows its ordinary entrypoint

#### Scenario: Powerspec is unavailable
- **WHEN** the pspec command cannot run
- **THEN** the agent reports Powerspec as unavailable instead of treating the skill as unsupported

### Requirement: Pending choices remain distinct from resolved guidance

A supported resolution SHALL identify whether it is resolved or pending. A pending result SHALL identify unanswered choices, suggested defaults, the owning answer location when available, and how to answer and rerun the same explicit-location invocation. The agent SHALL obtain required answers before dependent instructions; a suggestion, silence or elapsed time SHALL NOT count as an answer. A resolved result SHALL supply the relevant content directly. Resolution SHALL remain non-interactive.

#### Scenario: Framework choice is unresolved
- **WHEN** a supported skill needs a framework choice not supplied by configuration or defaults
- **THEN** the result is pending, not null, and instructions depending on that choice are not presented as selected guidance

#### Scenario: Answers are supplied
- **WHEN** the agent reruns the same selected-location invocation after an explicit answer is available
- **THEN** resolution uses that answer and returns the applicable instructions

#### Scenario: Selected path contains spaces
- **WHEN** a pending invocation targets a skill path containing spaces
- **THEN** the displayed rerun preserves that complete path and the agent/change selectors without falling back to name-based discovery

#### Scenario: Suggested default is not an answer
- **WHEN** a pending result offers a suggested default and the user has not answered
- **THEN** the agent does not follow instructions that depend on that choice

#### Scenario: Resolved content is self-contained
- **WHEN** resolution returns a resolved result
- **THEN** the relevant skill content is supplied directly without requiring each referenced file to be retrieved separately

#### Scenario: Resolution never prompts or records answers
- **WHEN** a skill invocation is pending
- **THEN** resolution neither reads answers from stdin nor writes answers itself

### Requirement: Skill lookup defaults to Markdown with optional JSON

Without --json, resolved output SHALL be the assembled skill Markdown on stdout with no JSON envelope or outer fence, and pending output SHALL be Markdown headed `Powerspec skill resolution pending` with questions and answer/rerun instructions, withholding the procedure. With --json, resolved output SHALL be an object with status resolved and the same Markdown as content; pending output SHALL have status pending and questions. Both formats SHALL share one outcome and exit-status contract.

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

#### Scenario: Failure output
- **WHEN** resolution fails in either format
- **THEN** it exits nonzero with diagnostics on stderr, emits no successful result, and keeps progress on stderr

### Requirement: Native agent selection owns skill precedence

For native invocation, the agent SHALL own skill discovery and selection, including precedence among user, project and other native locations. Powerspec SHALL consume the supplied location without a second lookup, scope ranking, registry check, or a scope question merely because several copies exist. Profile scope SHALL determine provisioning destination only, catalog annotations SHALL NOT replace native selection, and provisioning ownership checks SHALL stay separate from content assembly.

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

### Requirement: Ordinary native skills need no Powerspec call

For ordinary native invocation the agent SHALL discover and select skills through its native integration, without a universal pre-skill lookup or a Powerspec call before following an ordinary skill. Generated guidance SHALL identify mentioned manifest-backed skills that need Powerspec content assembly, and bundled dynamic entrypoints SHALL support direct native invocation. A needed pspec: target SHALL use the catalog route even when the selected catalog skill is ordinary.

#### Scenario: Guidance names manifest-backed skills
- **WHEN** generated guidance mentions a skill that has a Powerspec manifest
- **THEN** it identifies that skill as needing Powerspec content assembly

#### Scenario: Dynamic entrypoint is invoked natively
- **WHEN** the agent's native integration invokes a bundled dynamic entrypoint
- **THEN** the entrypoint supports that direct invocation

#### Scenario: Ordinary catalog target still uses the catalog route
- **WHEN** the task needs a pspec: target whose catalog skill has no manifest
- **THEN** the agent retrieves it through the catalog route rather than native lookup

### Requirement: Native-path resolution uses the exact selected location

For dynamic assembly, the agent SHALL give `pspec resolve skill` the exact selected location from the task working directory with its actual agent identity, passing an explicit active change via --change, including on reruns, and omitting it otherwise. That invocation SHALL NOT discover, activate or execute the skill. The bootstrap helper SHALL stay ordinary, never recursively resolved. A missing selected path SHALL be reported as missing handoff input, not replaced by a search or catalog path.

#### Scenario: No active change
- **WHEN** a dynamic invocation has no explicitly supplied active change
- **THEN** the agent omits --change

#### Scenario: Resolution does not run the skill
- **WHEN** pspec resolve skill assembles content for a selected location
- **THEN** it does not discover, activate or execute that skill

### Requirement: Explicit pspec invocations select catalog content

An explicit pspec: invocation SHALL select Powerspec catalog content through --ref independently of native copy precedence. That namespace SHALL NOT serve as a fallback for a missing native-selected path, and a missing catalog resource SHALL NOT trigger installation or substitution of a native copy.

#### Scenario: Missing native path does not fall back to the catalog
- **WHEN** a native-selected skill location is missing
- **THEN** the agent reports the missing location instead of retrieving the catalog copy

#### Scenario: Missing catalog resource is not substituted
- **WHEN** a pspec: target has no catalog resource
- **THEN** resolution reports it without installing or substituting a native copy

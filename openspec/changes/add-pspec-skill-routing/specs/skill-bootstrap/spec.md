# Spec Delta

## MODIFIED Requirements

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


## ADDED Requirements

### Requirement: Bootstrap routes needed Powerspec skill content

When the user requests pspec:<name-or-qualified-reference>, or applicable configured scenario guidance identifies that target as needed for the current task, bootstrap SHALL run pspec resolve skill --ref with that selector and the actual invoking agent from the task working directory. Presence of a reference in guidance SHALL NOT trigger retrieval before its owning task condition applies. Bootstrap SHALL search only the current consumer's effective profile selections, including resolve-only selections. An explicit active change SHALL be forwarded and retained on retries; no change SHALL be inferred. Bootstrap itself SHALL remain an ordinary native-discoverable skill and SHALL NOT recursively resolve itself merely to learn the routing procedure.

Bootstrap SHALL follow resolved catalog content directly and use the returned source root for supporting resources. It SHALL not repeat assembly because a resolved dynamic entrypoint contains native handoff instructions. For pending results it SHALL obtain only required missing answers, preserve confirmed answers and the exact returned reference on retry, and withhold dependent work. Suggestions, preselection, elapsed time, and silence SHALL NOT be treated as answers. Missing consumers, unknown or unselected references, ambiguous names, unavailable sources, invalid manifests, and unavailable commands SHALL remain explicit failures without native-installation, guessed-path, or ordinary-content fallback.

If owning guidance explicitly permits continuing separate work when the skill or its tooling is unavailable, bootstrap SHALL report the limitation and preserve that permitted fallback. It SHALL NOT present the fallback as successful resolution, follow an unresolved dynamic procedure, or claim a memory check that did not occur. Bootstrap SHALL retrieve supporting resources and other skill procedures only when the active task or selected procedure actually requires them, without speculative loading of sibling scenarios.

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

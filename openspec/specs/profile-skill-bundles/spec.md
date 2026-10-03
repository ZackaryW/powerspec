# Profile Skill Bundles Specification

## Purpose

Compose reusable resource references, defaults, and installation targets from configured catalogs without activating workflows or writing agent installations.

## Requirements

### Requirement: Global profiles mount unless explicitly excluded

A profile marked global = true SHALL participate automatically, including when the consumer has no selected profile or an empty profile string, unless explicitly excluded by the selected profile or the consumer. Empty selection SHALL contribute no selected-profile defaults or resources while retaining all eligible global contributions. Global discovery SHALL use configured resource catalogs rather than searching arbitrary repositories. Explicit exclusions SHALL use exclude-profiles with qualified profile identities in selected profiles or consumer configuration. A global profile SHALL be mounted once even if explicitly referenced. Explicit selection of an excluded profile SHALL report a configuration conflict. Exclusion SHALL remove its contributed defaults and resources without silently reintroducing them through automatic mounting. Mounting SHALL not execute a skill.

#### Scenario: Normal builtin mount
- **WHEN** the Python CLI profile is selected and the global builtin profile is not excluded
- **THEN** its effective bundle includes bootstrap from the global profile and TDD from the selected profile

#### Scenario: Empty profile selection
- **WHEN** the consumer omits profile or supplies an empty string
- **THEN** global profiles and their shared descendants compose after exclusions for init, sync, and runtime skill resolution
- **AND** the selected-profile default tier is empty

#### Scenario: Explicit global exclusion
- **WHEN** the consumer excludes the builtin global profile
- **THEN** it contributes no automatic bootstrap selection or defaults
- **AND** the result does not pretend bootstrap is active because a previous installation happens to remain

### Requirement: Profiles reference resources and supply defaults

Profiles SHALL reference contexts and traits through separate optional lists of qualified resource-reference strings. Skills SHALL use qualified resource references for packaged or registered catalog resources and `<source-alias>/<path-pattern>` strings for direct paths in a declared Git source. Profiles SHALL provide defaults without copying resource definitions or runtime answers. Explicit project values SHALL override selected-profile defaults, which SHALL override global-profile defaults. Conflicting same-precedence defaults, unknown source aliases, or ambiguous resource identities SHALL be diagnosed rather than silently selected by traversal order. Repeated skill installations SHALL be deduplicated by resolved identity, target agent, scope, and project root where applicable. Distinct installation scopes SHALL NOT be collapsed. Excluding a profile SHALL not uninstall shared user-level skills as a side effect.

#### Scenario: Local override
- **WHEN** the global and selected profiles supply defaults and the project overrides a key
- **THEN** the effective input layers expose the project value without modifying either profile or any installed skill

#### Scenario: Shared skill remains installed
- **WHEN** a project stops selecting a profile used elsewhere
- **THEN** composition changes for that project without removing another project's shared user-level skill

#### Scenario: Declared source shorthand
- **WHEN** a profile declares source alias `tools` and lists `tools/skills/*`
- **THEN** composition treats it as a direct selection from that declared source rather than a packaged or local catalog reference

### Requirement: Python CLI bundle makes TDD available without BDD

The first bundle SHALL combine Python CLI project-description guidance and defaults with TDD skill availability. It SHALL NOT select a BDD skill or evaluate BDD inputs. The shared TDD procedure SHALL live in SKILL.md, with Python additions placed through the skill's pspec.toml dynamic entries rather than always-published OpenSpec instructions. A profile language default SHALL remain overridable by consumer and temporal values. Other historical traits and bundles SHALL require separate review rather than automatic migration into this bundle.

The Python CLI profile SHALL supply language = "python", cli_framework = "typer", build_tool = "uv", test_runner = "pytest", and test_command = "uv run pytest" as overridable defaults. The Python CLI context SHALL declare typed compile-time inputs, with matching fallbacks for framework, build tool, runner, and test command. utility_path SHALL be supplied by persistent configuration or a profile rather than assuming a package name. Guidance SHALL cover CLI contracts, thin command handlers, utility responsibilities, and verification proportional to the changed boundary. Its TDD reference SHALL apply to behavior implementation, not environment-only work, documentation, or investigation; the skill procedure itself SHALL remain outside compiled context.

The Python CLI profile SHALL reference @builtin/utils-planning-aware through its profiles list. The resulting bundle SHALL include utility planning and utility-before-wiring guidance and the pspec-plan-utilities skill, retaining a single same-target pspec-tdd contribution when both profiles reference it.

#### Scenario: Python CLI tooling defaults
- **WHEN** the Python CLI profile is selected without tooling overrides
- **THEN** its effective defaults identify Typer, uv, pytest, and uv run pytest without prompting or installing those tools

#### Scenario: Consumer provides utility location
- **WHEN** the consumer declares utility_path = "src/powerspec/utils"
- **THEN** the context uses that location without requiring the directory to be created before utility work needs it

#### Scenario: Environment-only session
- **WHEN** the Python CLI bundle is selected but the session only repairs an environment
- **THEN** TDD remains available without mode questions, skill execution, or testing-procedure injection into OpenSpec

#### Scenario: TDD invocation
- **WHEN** the user or calling workflow selects TDD in that project
- **THEN** composition supplies the TDD resource identity and defaults for the skill resolver, without installing or executing it

### Requirement: Compile-time context values resolve without interaction

Compile-time declarations SHALL specify an id and type, with optional choices and default. Effective values SHALL follow consumer config.toml [vars], selected-profile defaults, global-profile defaults, then the declaration's default. Compile-time resolution SHALL NOT prompt or consume current.toml. Missing or invalid required values SHALL produce configuration diagnostics rather than activating a runtime question or falling back from an invalid explicit value. This contract describes inputs to future context compilation; it does not require implementing general synchronization in this change.

#### Scenario: Context fallback is used
- **WHEN** no persistent or profile layer supplies build_tool and its declaration defaults to uv
- **THEN** compile-time resolution uses uv without interaction

#### Scenario: Temporal value does not change compiled configuration
- **WHEN** current.toml contains a different value for a declared compile-time key
- **THEN** compile-time resolution ignores that temporal value and follows persistent/default precedence

#### Scenario: Missing utility path
- **WHEN** no persistent or profile value supplies the required utility_path and no declaration default exists
- **THEN** compile-time resolution reports the missing value without prompting

#### Scenario: Invalid explicit framework
- **WHEN** persistent configuration supplies a value outside cli_framework choices
- **THEN** compile-time resolution reports the invalid value without prompting or silently selecting Typer

### Requirement: Contexts and traits have distinct evaluation ownership

Catalogs SHALL expose compile-time contexts under contexts/ and runtime traits under traits/. Profiles SHALL select them through separate contexts and traits lists alongside skills and vars. The referencing list SHALL identify the resource kind; a context and trait with the same source/name SHALL remain distinct identities. Context resources SHALL declare attach destinations and optional compiletime inputs and per-attachment when conditions for future config.yaml synchronization. Runtime traits SHALL declare hooks and a guidance body, with an optional top-level when condition, for event-time resolution. Neither resource SHALL require or accept a mode discriminator.

Context resources SHALL reject hooks and a top-level runtime body/when. Runtime traits SHALL reject attach destinations and compiletime inputs. Mixed resource shapes and legacy config/hook mode declarations SHALL produce migration diagnostics rather than silently changing ownership. Profiles SHALL NOT own attachment destinations or hook selectors. Composition SHALL retain both resource kinds without compiling contexts, dispatching traits, or executing skills.

#### Scenario: Python CLI context is selected
- **WHEN** a profile selects @builtin/python-simple-cli through its contexts list
- **THEN** its attachments are retained for compilation and are not returned by runtime trait dispatch

#### Scenario: Bootstrap runtime trait is selected
- **WHEN** a profile references a bootstrap trait through its traits list
- **THEN** its hooks and body remain exclusively runtime contributions

#### Scenario: Same name in different resource kinds
- **WHEN** one source contains a context and trait with the same name and a profile selects each through the appropriate list
- **THEN** each resolves to its declared kind without a name collision or inferred conversion

#### Scenario: Legacy config-mode trait
- **WHEN** a resource in traits/ declares mode = "config" and attach destinations
- **THEN** validation explains its required migration to contexts/ and the profile contexts list instead of treating it as a runtime trait

### Requirement: Guidance conditions use Python expressions

Context attachment entries and top-level runtime trait bodies SHALL support an optional when string containing one Python expression. Omission SHALL be unconditional. Conditions SHALL retain ordinary Python expression semantics, including Boolean combinations, comparison, indexing, method calls, and short-circuit order. Results SHALL be actual Booleans; non-Boolean results and syntax/name/evaluation errors SHALL produce resource/contribution diagnostics instead of truthiness coercion, false, or ordinary fallback.

Composition SHALL validate condition shape and syntax without running expressions/capabilities. Legacy [[check]] declarations and check-ID when maps SHALL be rejected with migration diagnostics. Bodies/defaults/ordinary TOML strings SHALL NOT be executed as code. Skill-manifest equality-map guards and typed hint detectors SHALL retain their separate contract.

#### Scenario: CodeGraph condition
- **WHEN** an eligible trait evaluates which('codegraph') is not None and (git_root / '.codegraph').is_dir()
- **THEN** it contributes only when executable discovery and the Git-root directory observation satisfy the expression, without treating the marker as index health

#### Scenario: Short-circuit avoids a probe
- **WHEN** which('zmem') returns None in a condition combining presence with run_json using and
- **THEN** the condition returns false without executing the right-hand probe

#### Scenario: Non-Boolean return
- **WHEN** a condition returns a path, list, number, or other non-Boolean value
- **THEN** evaluation diagnoses it instead of including guidance through truthiness

#### Scenario: Legacy check surface
- **WHEN** a context or trait declares [[check]] or a check-ID map in when
- **THEN** validation explains migration to a Python expression rather than maintaining two condition languages

#### Scenario: Plain text remains data
- **WHEN** body/default text resembles a Python expression
- **THEN** it remains data without execution

### Requirement: Condition bindings follow resource ownership

Each evaluation SHALL receive explicit capabilities named which, git_root, vars, run_json, and armed. which SHALL discover executables using the invocation environment, returning their path or None without launching them. git_root SHALL provide the caller's enclosing Git-root path, including worktrees, never a source catalog or skill home. Required unavailable context SHALL be diagnosed rather than guessed.

vars SHALL expose effective values in a separate read-only mapping without shadowing capabilities. Contexts SHALL use persistent shared/profile/declaration values, excluding temporal/change overrides. Runtime traits SHALL use runtime shared layers plus change layers only with an explicit caller selector. Evaluation SHALL NOT prompt for skill inputs or substitute stored values for actual capability results. Names not provided SHALL NOT become implicitly available.

Conditions SHALL be documented as trusted executable rules with host capabilities, not isolated untrusted code. Fresh bindings SHALL NOT be described as deep object isolation, filesystem confinement, complete execution-time limits, or rollback of callback effects. Powerspec evaluation plumbing SHALL NOT itself persist results, install assets, or prompt.

#### Scenario: Persistent values control a context
- **WHEN** vars['language'] == 'python' is evaluated with persistent/default python and temporal rust
- **THEN** the context condition uses python without reading the temporal override

#### Scenario: Runtime change scope
- **WHEN** a trait reads a winning matching-change variable with that change explicitly selected by the caller
- **THEN** vars follows runtime precedence without borrowing another change's values

#### Scenario: Variable keys do not replace capabilities
- **WHEN** project variables contain which or run_json keys
- **THEN** they remain inside vars and actual executable/probe capabilities stay independently bound

#### Scenario: Worktree owns the observation
- **WHEN** a condition uses git_root from a worktree invocation
- **THEN** it receives that worktree root rather than the main checkout or catalog root

#### Scenario: Trusted callback has effects
- **WHEN** selected trusted code calls a side-effecting method/callback and later raises
- **THEN** evaluation reports the failure without claiming its host effects were isolated or rolled back

### Requirement: Command JSON conditions distinguish data from probe failures

run_json SHALL accept a nonempty list of string argv items, execute without a shell in the invocation cwd/environment, and return stdout parsed as a JSON object after exit zero. Its default subprocess timeout SHALL be five seconds. A caller operating under a shorter externally enforced deadline SHALL be able to supply a finite positive timeout no greater than that default; runtime hook delivery SHALL use a timeout short enough to leave cleanup and serialization time before its native callback deadline. Invalid arguments, missing executables, nonzero exits, timeout, invalid JSON, and non-object JSON SHALL produce diagnostics instead of readiness false or successful condition output. A valid object SHALL remain data for the expression to assess; process success alone SHALL NOT imply readiness. The helper timeout SHALL NOT be advertised as a complete expression execution limit.

#### Scenario: Service doctor reports a problem
- **WHEN** zmem service doctor exits zero with ok=false and the expression tests .get('ok') is True
- **THEN** run_json returns the object and the condition evaluates false

#### Scenario: Missing ok field
- **WHEN** a successful probe returns an object without ok and the expression tests .get('ok') is True
- **THEN** the condition evaluates false without inventing positive readiness

#### Scenario: Hook boundary supplies a smaller budget
- **WHEN** runtime hook delivery evaluates run_json under a five-second native callback deadline
- **THEN** the subprocess receives a smaller positive timeout and leaves time for the dispatcher to diagnose or serialize its result

#### Scenario: Probe cannot produce data
- **WHEN** a probe times out, exits nonzero, or produces invalid or non-object JSON
- **THEN** evaluation diagnoses the probe and resource instead of treating failure as normal false
### Requirement: Conditions execute only at their owning boundary

The foundation SHALL expose condition evaluation separately from composition. Eligible contributions SHALL be evaluated once per owning invocation with fresh namespaces and current capability context. Python calls SHALL retain authored order without implicit probe caching. Results SHALL NOT be persisted or reused across invocations.

Sync SHALL evaluate contexts while compiling a snapshot valid until another sync. Hooks SHALL evaluate matching non-excluded traits only at mapped Powerspec lifecycle callbacks. False SHALL omit only its contribution without removing other guidance, skills, or native registrations. Context publication and configuration or expression authoring errors SHALL remain atomic and yield no successful partial result. Runtime hook delivery MAY isolate an operational command-probe failure to its owning optional trait when it reports the diagnostic and preserves independent successfully resolved traits. Composition, native events without a Powerspec mapping, and ineligible contributions SHALL execute no conditions.

#### Scenario: Composition is machine-independent
- **WHEN** profiles with conditional contexts or traits are composed
- **THEN** expressions are retained without observations or subprocess execution

#### Scenario: Later calls observe availability
- **WHEN** a tool becomes available between matched runtime lifecycle callbacks
- **THEN** the later callback observes it without synchronization or a cached earlier result

#### Scenario: Ordinary prompt has no owning Powerspec boundary
- **WHEN** an established session receives an ordinary prompt without startup, clear, fork, or compact
- **THEN** no selected context or trait condition is evaluated

#### Scenario: False affects one contribution
- **WHEN** one condition returns false and another contribution is unconditional
- **THEN** only the guarded contribution is omitted, preserving skills and shared registrations

#### Scenario: Runtime probe failure is isolated
- **WHEN** an optional runtime trait's command probe fails after another trait resolves successfully
- **THEN** hook delivery diagnoses and omits the failing trait while retaining the independent guidance

#### Scenario: Error is not omission
- **WHEN** an eligible expression has invalid syntax, an unavailable required binding, or a non-Boolean result
- **THEN** the caller receives a resource-specific diagnostic instead of treating the authored error as normal false
### Requirement: Builtin is a reserved source namespace

The builtin source identity SHALL refer exclusively to Powerspec's packaged resources. External sources, whether local or remote, SHALL NOT register as builtin or shadow its catalog. A repository name, directory name, or external resource declaration SHALL NOT confer builtin identity. Resource discovery from a consumer's .pspec SHALL NOT implicitly make it part of the bundled catalog.

#### Scenario: Remote registration claims builtin
- **WHEN** an external source registration attempts to use builtin as its source identity
- **THEN** registration reports the reserved-name conflict without rebinding the bundled catalog

#### Scenario: External folder happens to be named builtin
- **WHEN** an externally registered source contains a repository or directory named builtin
- **THEN** it retains its external source identity rather than resolving as @builtin

### Requirement: Qualified skill references preserve declared installed names

A qualified skill reference SHALL identify a registered source and the skill name declared in SKILL.md. The source folder SHALL be treated as a location rather than the installed identity. Catalog resolution SHALL retain source provenance for downstream provisioning. Remote acquisition belongs to the remote-sources capability; catalog composition SHALL accept validated local materializations without requiring acquisition. Installation SHALL preserve the declared skill name without automatically prefixing it with the source identity. Duplicate declared skill names within one source SHALL be diagnosed as ambiguous.

#### Scenario: Bundled source folder differs from skill name
- **WHEN** @builtin/pspec-tdd resolves to a folder named pspec_tdd with SKILL.md name pspec-tdd
- **THEN** its declared and installed skill identity is pspec-tdd

#### Scenario: Registered source selected
- **WHEN** a profile selects a skill from a validated registered local catalog
- **THEN** composition retains its declared skill name, source identity, and resource location for downstream provisioning

### Requirement: Installation name conflicts depend on selected resources

Multiple registered sources MAY contain skills with the same declared name. Registration alone SHALL NOT constitute an installation conflict. If effective selections would install different skills under the same name for the same target agent, scope, and project root where applicable, installation selection SHALL report the conflicting source identities instead of choosing by traversal order, renaming the skills, or overwriting one with another. Existing installation conflict protections SHALL remain applicable across projects.

#### Scenario: Same name exists in an unselected source
- **WHEN** two registered sources contain pspec-tdd but only one is selected for installation
- **THEN** the unselected resource does not create a selection conflict

#### Scenario: Different same-name skills are both selected
- **WHEN** effective profiles select different skills named pspec-tdd from two sources for the same target agent, scope, and project root where applicable
- **THEN** selection reports both source identities as conflicting without installing one over the other

#### Scenario: Same name at distinct installation scopes
- **WHEN** effective profiles select a user-scoped and a project-scoped skill with the same installed name
- **THEN** their distinct destinations do not create an installation-name conflict
- **AND** the native agent owns selection when the skill is invoked

### Requirement: One profile declares one skill installation scope

A profile SHALL declare a single top-level scope of user or project applying to every skill it declares. Omitted scope SHALL default to user. Skill references SHALL remain strings; per-skill scope overrides SHALL NOT be supported. Invalid scope values SHALL be diagnosed rather than inferred. Composing profiles SHALL preserve the declaring profile's scope for each contribution, including global profiles. The global flag SHALL govern mounting independently of installation scope. Scope SHALL govern installation only, not runtime selection between installed copies. Native agent precedence SHALL remain authoritative. User/project coexistence SHALL NOT itself constitute a Powerspec conflict or require a scope-choice prompt. Scope SHALL NOT relocate context destinations or generic hook dispatchers.

#### Scenario: Project-scoped skill bundle
- **WHEN** a profile declares scope = "project" and two skills
- **THEN** both skills retain project-scoped target descriptors requiring the explicit project root for downstream ZuAT provisioning

#### Scenario: User-scoped global profile and project-scoped selected profile
- **WHEN** the user-scoped builtin profile composes with a project-scoped selected profile
- **THEN** builtin skills retain user scope and the selected profile's skills retain project scope

#### Scenario: Scope omitted
- **WHEN** a profile lists skill references without a scope field
- **THEN** all of that profile's skills default to user scope

### Requirement: Profiles compose referenced subprofiles

A profile SHALL support an optional top-level profiles list of qualified profile-reference strings. Composition SHALL resolve these references recursively without copying resources, mount each resolved profile once, and retain each declaring profile's installation scope and provenance. Missing references and direct or indirect cycles SHALL be diagnosed with the reference chain rather than silently omitted or partially composed.

Profiles reached through the explicitly selected root SHALL supply selected-tier defaults; profiles reached only through automatic globals SHALL supply global-tier defaults. An identity reached through both SHALL contribute once at the selected tier. Parent/child depth and declaration order SHALL NOT create another default precedence layer; unequal values at the same tier SHALL use the existing conflict diagnostic.

The consumer's and explicitly selected root's exclude-profiles SHALL apply before contributions are expanded. Excluding the explicitly selected root SHALL be a conflict. Excluding a nested profile SHALL omit it and descendants reachable only through that branch, without removing a descendant reachable through another non-excluded path. Subprofiles and automatic globals SHALL NOT contribute another exclusion layer; their own exclude-profiles SHALL apply when explicitly selected as a root. An excluded identity SHALL NOT be restored by another reference or automatic mounting.

#### Scenario: Python CLI includes utility planning
- **WHEN** python-simple-cli references @builtin/utils-planning-aware
- **THEN** composition includes the child profile's two contexts and planning/TDD skills alongside the parent's resources without copying them

#### Scenario: Shared subprofile
- **WHEN** two branches reference the same child and both parent and child select the same skill for the same target
- **THEN** the child contributes once and the skill target is deduplicated

#### Scenario: Child retains scope
- **WHEN** a project-scoped parent includes a user-scoped child
- **THEN** the child's declared skills retain user scope while the parent's declared skills retain project scope

#### Scenario: Parent and child defaults disagree
- **WHEN** a selected parent and its child supply unequal values for the same default key
- **THEN** composition reports a same-tier conflict rather than choosing by depth or list order

#### Scenario: Selected and global reachability
- **WHEN** one profile is reachable from both the selected root and an automatic global
- **THEN** it contributes once at the selected tier

#### Scenario: Missing or cyclic reference
- **WHEN** a profile reference is missing or returns to an ancestor in the active reference chain
- **THEN** composition reports the failed chain without returning a successful partial bundle

#### Scenario: Excluded child shares a descendant
- **WHEN** the root excludes child A while A and non-excluded child B both reference C
- **THEN** A and its exclusive descendants contribute nothing, while C remains eligible through B

#### Scenario: Nested exclusions do not create hidden policy
- **WHEN** an included child declares exclude-profiles but is not the explicitly selected root
- **THEN** those exclusions do not modify this composition; the consumer and selected root determine exclusions

### Requirement: Utility planning and implementation ordering form a reusable bundle

The utils-planning-aware profile SHALL reference separate utility-plan and utility-apply contexts and supply pspec-plan-utilities and pspec-tdd as skills. It SHALL NOT impose language-specific defaults. The planning context SHALL attach skill invocation and contract/reuse assessment guidance to rules.design and utility-before-dependent-wiring task ordering to rules.tasks. The apply context SHALL attach to operations.apply.guidance and direct implementation and verification of accepted utility contracts through TDD before dependent application wiring, followed by integration verification.

The guidance SHALL define utilities as generic helpers usable by other projects through portable inputs and outputs. It SHALL require a concrete use outside the current project and domain-neutral helper verification. Application models, profile/configuration policy, and workflow rules SHALL remain with application callers; internal reuse alone SHALL NOT classify an application service as a utility. The guidance SHALL reuse existing suitable utilities, avoid artificial utility work, and exclude environmental, documentation, and configuration work without behavioral effects. Planning SHALL NOT authorize implementation. Utility verification SHALL NOT claim application integration is complete. These contexts SHALL reuse existing destinations without adding a schema artifact or embedding skill procedures. Foundation composition SHALL retain this source guidance without executing it or publishing config.yaml; publication remains future sync work.

#### Scenario: Necessary utility behavior
- **WHEN** the reusable profile's context resources are composed for a behavior change needing utility work
- **THEN** the design/task attachments specify utility contracts and ordered work, and the apply attachment specifies verified utilities before dependent wiring and later integration checks

#### Scenario: No utility work
- **WHEN** the selected task only changes environment setup or existing APIs already satisfy the necessary utility responsibilities
- **THEN** the guidance does not require invented utilities or a manufactured TDD cycle

#### Scenario: Portable helper and application policy
- **WHEN** a change needs nearest configuration discovery and profile composition
- **THEN** the utility plan identifies reusable file-discovery or graph mechanics where needed, while configuration ownership and profile policy remain application responsibilities
- **AND** helper contracts and tests use ordinary paths or graph identifiers without depending on Powerspec models

### Requirement: Conditions can query selected resources

Conditions SHALL expose armed(kind, reference) returning a Boolean for membership in the invoking consumer's effective bundle after composition, exclusions, and deduplication. Supported kinds SHALL be skill, trait, context, and profile, with distinct identity namespaces. Queries SHALL use exact qualified resource identities under the existing identity contract; skill identities SHALL respect declared skill names and resolved remote contributions SHALL be queryable by their concrete source-relative identities. Retained global/subprofiles SHALL count as selected. An exact valid identity absent from the bundle SHALL return false without loading/acquiring sources or inspecting installations.

The snapshot SHALL be computed before condition evaluation. Membership SHALL NOT depend on event match, condition result, successful context compilation, installation, skill resolution, or execution. Queries SHALL NOT evaluate referenced resources, mutate selection, or remove native assets. Self and mutual queries SHALL NOT recurse. Context callers SHALL use their sync-time selection snapshot; trait callers SHALL use their current invocation's snapshot. Variables SHALL NOT shadow armed. Invalid kinds, malformed or unqualified references, wildcards, and invalid argument types SHALL produce diagnostics. Failure to compose the effective bundle SHALL remain an error rather than false membership.

#### Scenario: All supported kinds
- **WHEN** the effective bundle contains a selected skill, trait, context, and retained profile
- **THEN** each exact query in its respective kind returns true, while an absent identity returns false
- **AND** a context and trait sharing a source/name are queried independently

#### Scenario: Profile exclusions and shared descendants
- **WHEN** a profile is excluded and one descendant remains reachable through another selected profile
- **THEN** the excluded profile and its exclusive contributions are not armed, while the retained descendant and its contributions remain armed

#### Scenario: Selection differs from activation
- **WHEN** a selected trait has a false condition or does not match the current event, a selected context emits no guidance, or a selected skill is not installed
- **THEN** armed still reports their selected identities as true without evaluating them

#### Scenario: Self and mutual queries
- **WHEN** selected traits query themselves or one another through armed
- **THEN** the results are membership checks on the same immutable selection snapshot without recursion or declaration-order dependence

#### Scenario: Include or omit a contribution
- **WHEN** an attachment or trait uses armed combined with Python not, and, or or
- **THEN** its resulting Boolean controls only that contribution, leaving effective selection and native installations unchanged

#### Scenario: Invalid query and unavailable optional source
- **WHEN** a query has an invalid kind, malformed/unqualified identity, wildcard, or invalid argument type
- **THEN** evaluation reports a contribution diagnostic rather than treating the query as false
- **WHEN** a syntactically valid exact reference to an unselected source is queried
- **THEN** it returns false without acquisition; an actual selected-source resolution failure remains a composition error

#### Scenario: Fresh selection at the owning boundary
- **WHEN** selection changes between invocations
- **THEN** the next hook query uses the new snapshot, while previously published context text changes only after sync

### Requirement: Authored configuration uses strict typed boundaries

Profile, context, trait, and compile-time declaration inputs SHALL be validated using strict Pydantic v2 models after TOML decoding. Unknown structural fields and invalid declared defaults or choices SHALL fail with location diagnostics. Variable mappings SHALL permit arbitrary names and native values. Identity, graph, and resolution policy SHALL remain application logic.

#### Scenario: Invalid declaration default
- **WHEN** an integer declaration supplies a Boolean default
- **THEN** catalog loading reports an error instead of coercing it to an integer

#### Scenario: Unknown structural field
- **WHEN** a profile contains an unsupported top-level field
- **THEN** catalog loading reports the field rather than silently ignoring it

### Requirement: Utility planning considers mature packages

The utils-planning-aware bundle SHALL select a mature-package-inspection runtime trait guarded by selection of the planning skill. Its reminder SHALL apply to relevant utility planning and SHALL NOT initiate planning or installation. The skill SHALL assess existing implementations and relevant mature third-party public APIs proportionally before choosing direct reuse, adaptation, or custom mechanics, with concrete contract-fit evidence.

#### Scenario: Utility bundle selected
- **WHEN** Python CLI composes utils-planning-aware
- **THEN** the package-inspection trait and planning skill are selected together, with no workflow executed during composition

# Profile Skill Bundles Specification

## Purpose

Compose reusable resource references, defaults, and installation targets from configured catalogs without activating workflows or writing agent installations.

## Requirements

### Requirement: Global profiles mount unless explicitly excluded

A profile marked global = true SHALL participate automatically, including with no or an empty selected profile, unless the selected profile or consumer excludes it through exclude-profiles with qualified identities. Empty selection SHALL contribute no selected-profile defaults or resources while keeping eligible globals. Global discovery SHALL use configured catalogs, not arbitrary repositories, and a global profile SHALL mount once even if referenced. Mounting SHALL NOT execute a skill.

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

#### Scenario: Selecting an excluded profile conflicts
- **WHEN** a profile is both explicitly selected and excluded
- **THEN** composition reports a configuration conflict

#### Scenario: Excluded global is not remounted
- **WHEN** a global profile is excluded
- **THEN** its defaults and resources are removed and automatic mounting does not reintroduce them

### Requirement: Profiles reference resources and supply defaults

Profiles SHALL reference contexts and traits through separate optional lists of qualified references. The optional skills and resolve-skills lists SHALL use qualified references for catalog resources and `<source-alias>/<path-pattern>` for declared Git sources; skills SHALL select for native installation and Powerspec resolution, and resolve-skills only for Powerspec resolution. Both lists SHALL share the profile graph after exclusions, keep provenance and need matching source declarations.

#### Scenario: Local override
- **WHEN** the global and selected profiles supply defaults and the project overrides a key
- **THEN** the effective input layers expose the project value without modifying either profile or any installed skill

#### Scenario: Shared skill remains installed
- **WHEN** a project stops selecting a profile used elsewhere
- **THEN** composition changes for that project without removing another project's shared user-level skill

#### Scenario: Declared source shorthand
- **WHEN** a profile declares source alias `tools` and lists `tools/skills/*`
- **THEN** composition treats it as a direct selection from that declared source rather than a packaged or local catalog reference

#### Scenario: Resolve-only skill is selected
- **WHEN** an effective profile declares a resource only in resolve-skills
- **THEN** explicit Powerspec lookup can select that resource without adding it to the agent's installation targets

#### Scenario: Same resource has both selections
- **WHEN** one retained profile selects a resource through resolve-skills and another selects it through skills
- **THEN** the resource has one catalog identity and retains the requested installation target with its declaring scope

### Requirement: Python CLI bundle makes TDD available without BDD

The first bundle SHALL combine Python CLI guidance and defaults with TDD skill availability, without selecting a BDD skill or evaluating BDD inputs. The shared TDD procedure SHALL live in SKILL.md, with Python additions placed through its pspec.toml dynamic entries rather than always-published OpenSpec instructions. A profile language default SHALL remain overridable by consumer and temporal values. Other historical traits and bundles SHALL need separate review, not automatic migration into it.

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

Compile-time declarations SHALL specify an id and type, with optional choices and default. Effective values SHALL follow consumer config.toml [vars], selected-profile defaults, global-profile defaults, then the declaration default, without prompting or consuming current.toml. Missing or invalid required values SHALL produce configuration diagnostics, not runtime questions or fallback from an invalid explicit value.

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

Catalogs SHALL expose compile-time contexts under contexts/ and runtime traits under traits/, selected through separate profile lists, so a same-named context and trait stay distinct. Contexts SHALL declare attach destinations, optional compiletime inputs and per-attachment when; traits SHALL declare hooks and a guidance body with an optional top-level when. Neither SHALL require or accept a mode discriminator; composition SHALL keep both without compiling, dispatching or executing.

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

Context attachment entries and top-level runtime trait bodies SHALL support an optional when string holding one Python expression, and omission SHALL be unconditional. Conditions SHALL keep ordinary Python semantics, including Boolean operators, comparison, indexing, method calls and short-circuiting, and SHALL return real Booleans; non-Boolean results and syntax, name or evaluation errors SHALL be diagnostics, never coerced, false or fallback.

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

#### Scenario: Composition validates without running
- **WHEN** a catalog with conditions is composed
- **THEN** condition shape and syntax are validated without running any expression or capability

#### Scenario: Skill manifest guards keep their own rules
- **WHEN** a skill manifest uses an equality-map guard or typed hint detector
- **THEN** that construct follows its separate contract rather than Python condition rules

### Requirement: Condition bindings follow resource ownership

Each evaluation SHALL receive only the capabilities which, git_root, vars, run_json and armed. which SHALL find executables in the invocation environment, returning a path or None without running them, and git_root SHALL give the caller's Git root, including worktrees, never a catalog or skill home. vars SHALL be a separate read-only mapping that cannot shadow capabilities. Contexts SHALL see persistent values only; traits SHALL see runtime layers plus change layers under an explicit selector.

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

#### Scenario: Missing required context is diagnosed
- **WHEN** a condition needs context that is unavailable, such as a Git root outside any repository
- **THEN** evaluation reports a diagnostic instead of guessing a value

### Requirement: Command JSON conditions distinguish data from probe failures

run_json SHALL take a nonempty string argv list, run without a shell in the invocation cwd and environment, and return stdout parsed as a JSON object after exit zero, with a five-second default timeout that callers MAY lower to a finite positive value; hook delivery SHALL leave cleanup and serialization time before its native deadline. Invalid arguments, missing executables, nonzero exits, timeouts and invalid or non-object JSON SHALL be diagnostics, not false. A valid object SHALL remain data.

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

#### Scenario: Process success is not readiness
- **WHEN** a probe exits zero with a valid JSON object
- **THEN** the object is data for the expression to assess and success alone does not mean the service is ready

#### Scenario: Helper timeout is not an expression limit
- **WHEN** run_json documentation describes its timeout
- **THEN** it is not presented as a complete execution limit for the whole expression

### Requirement: Conditions execute only at their owning boundary

Condition evaluation SHALL be separate from composition. Eligible contributions SHALL be evaluated once per owning invocation with fresh namespaces and current capabilities, in authored order without probe caching, and results SHALL NOT be persisted or reused. Sync SHALL evaluate contexts into a snapshot valid until another sync, and hooks SHALL evaluate matching non-excluded traits only at mapped callbacks. Composition, unmapped events and ineligible contributions SHALL execute no conditions.

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

A qualified skill reference SHALL identify a registered source and the skill name declared in SKILL.md, treating the source folder as a location, not the installed identity; catalog resolution SHALL keep source provenance. Catalog composition SHALL accept validated local materializations without acquisition, which belongs to remote-sources. Installation SHALL keep the declared name without a source prefix, and duplicate declared names within one source SHALL be diagnosed as ambiguous.

#### Scenario: Bundled source folder differs from skill name
- **WHEN** @builtin/pspec-tdd resolves to a folder named pspec_tdd with SKILL.md name pspec-tdd
- **THEN** its declared and installed skill identity is pspec-tdd

#### Scenario: Registered source selected
- **WHEN** a profile selects a skill from a validated registered local catalog
- **THEN** composition retains its declared skill name, source identity, and resource location for downstream provisioning

### Requirement: Installation name conflicts depend on selected resources

Multiple registered sources MAY contain skills with the same declared name, and registration alone SHALL NOT be an installation conflict. If effective selections would install different skills under one name for the same agent, scope and project root, selection SHALL report the conflicting sources instead of choosing by traversal order, renaming or overwriting. Existing installation conflict protections SHALL still apply across projects.

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

A profile SHALL declare one top-level scope of user or project, defaulting to user, applying to every installation target in its skills; resolve-skills entries SHALL have no scope or destination and SHALL NOT need a project root for that reason. Skill references SHALL stay strings without per-skill scope overrides, invalid scopes SHALL be diagnosed, and composition SHALL keep each declaring profile's scope, including for globals, independently of the global flag.

#### Scenario: Project-scoped skill bundle
- **WHEN** a profile declares scope = "project" and two skills
- **THEN** both skills retain project-scoped target descriptors requiring the explicit project root for downstream ZuAT provisioning

#### Scenario: User-scoped global profile and project-scoped selected profile
- **WHEN** the user-scoped builtin profile composes with a project-scoped selected profile
- **THEN** builtin skills retain user scope and the selected profile's skills retain project scope

#### Scenario: Scope omitted
- **WHEN** a profile lists installation references in skills without a scope field
- **THEN** all of that profile's installation targets default to user scope

#### Scenario: Project-scoped resolve-only profile
- **WHEN** a project-scoped profile declares a resolve-only skill and no installation targets
- **THEN** the resolve-only selection has no native destination or scope-choice requirement

### Requirement: Profiles compose referenced subprofiles

A profile SHALL support an optional top-level profiles list of qualified profile references. Composition SHALL resolve them recursively without copying resources, mount each resolved profile once, and keep each declaring profile's installation scope and provenance. Missing references and direct or indirect cycles SHALL be diagnosed with the reference chain rather than omitted or partially composed.

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

The utils-planning-aware profile SHALL reference separate utility-plan and utility-apply contexts and supply pspec-plan-utilities and pspec-tdd skills, without language-specific defaults. The planning context SHALL attach skill invocation and contract/reuse guidance to rules.design, and utility-before-wiring ordering to rules.tasks. The apply context SHALL attach to operations.apply.guidance, directing TDD of accepted utility contracts before dependent wiring, then integration verification.

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

Conditions SHALL expose armed(kind, reference), returning whether an exact qualified skill, trait, context or profile identity is in the invoking consumer's effective bundle after composition, exclusions and deduplication. Skill identities SHALL use declared names, remote contributions SHALL be queryable by source-relative identity, and retained globals and subprofiles SHALL count as selected. Skill membership SHALL include skills and resolve-skills without implying native availability.

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

#### Scenario: Resolve-only membership
- **WHEN** a retained profile selects an exact resource only through resolve-skills
- **THEN** armed reports that skill as selected without probing or creating an installation

#### Scenario: Absent identity is false without loading
- **WHEN** an exact valid identity is not in the effective bundle
- **THEN** armed returns false without loading or acquiring sources or inspecting installations

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

### Requirement: Guidance bodies can share one contained file

Context attachments and runtime traits SHALL accept exactly one of inline `body` or `body_file`, a UTF-8 file at a relative path inside the owning catalog root; absolute paths, traversal, escaping links, absent files and invalid text SHALL fail with located diagnostics. Loading SHALL resolve the body before reference classification, interpolation and condition processing, without merging context and trait timing or executing guidance. Inline resources SHALL remain valid.

#### Scenario: One instruction serves two destinations
- **WHEN** a context attachment and trait reference the same body file
- **THEN** both receive the same authored text and existing skill-reference classification applies

#### Scenario: Invalid body source
- **WHEN** both body forms, neither form, or an escaping/missing body file is declared
- **THEN** catalog loading fails with a located diagnostic

### Requirement: Zmem standing policy is selected for persistent and runtime delivery
The global zmem lifecycle profile SHALL select both a context and trait sharing one authoritative guidance body. The body SHALL require memory lookup when task history, provenance or prior decisions matter, followed by current-evidence verification, without requiring the user to name zmem. Excluding the profile SHALL remove both contributions. The rule SHALL preserve existing commit authorization and task-specific skill selection.

#### Scenario: Historical rationale question
- **WHEN** the selected profile's guidance is consumed for a question about when or why a decision changed
- **THEN** the guidance calls for zmem-query-memory without a separate permission question

#### Scenario: Profile excluded
- **WHEN** the consumer excludes the zmem profile
- **THEN** neither persistent nor runtime zmem guidance is selected

### Requirement: Resolve-only selection preserves lifecycle boundaries

Init and upgrade SHALL prepare or refresh remote selections from both skills and resolve-skills. Runtime resolution, status and hooks SHALL NOT acquire or refresh sources. Only skills contributions SHALL create native targets or obsolete-copy evidence. Resolve-only changes SHALL NOT install, adopt, update or remove native copies. Native handoff tokens SHALL require installation selections; resolve-only targets SHALL use literal pspec: guidance.

#### Scenario: Prepare and refresh a resolve-only remote source
- **WHEN** a consumer selects a remote resource only through resolve-skills
- **THEN** init can prepare its missing source and upgrade can explicitly refresh it while creating no native target for that resource

#### Scenario: Switch an installation selection to resolve-only
- **WHEN** a profile replaces its skills entry with resolve-skills and a native copy already exists
- **THEN** the new selection is resolvable without adopting, rewriting, or uninstalling that existing copy solely because its declaration changed

#### Scenario: Native handoff cannot promise an uninstalled resource
- **WHEN** authored guidance uses <skill:helper> but helper is selected exclusively through resolve-skills
- **THEN** publication or eligible hook rendering diagnoses the reference and directs use of pspec:helper instead of instructing native discovery

#### Scenario: Explicit reference remains literal guidance
- **WHEN** authored guidance contains pspec:helper for a resolve-only skill
- **THEN** the text is delivered without a native dynamic-handoff heading or executing that skill during rendering

#### Scenario: Preserve ownership and deferred native boundaries
- **WHEN** source or delivery declarations change
- **THEN** existing installation ownership and recovery checks remain in force
- **AND** resolve-only selections do not advertise native discoverability or independently authorize adoption, updates or removal of retained native copies

### Requirement: Resolve-only selection means availability rather than session loading

resolve-skills SHALL make procedures available for relevant scenarios or user requests without requesting them for the agent during selection, composition, source preparation or status inspection. It SHALL NOT add native installation targets. Lightweight owning guidance SHALL express applicability and target references without embedding procedures, preserving shared body_file support and separate persistent/runtime evaluation timing.

#### Scenario: Several scenario skills are selected
- **WHEN** a profile selects bootstrap for native installation and A, B, and C only through resolve-skills
- **THEN** those three skills are available for later retrieval without native installation targets or eager procedural delivery

#### Scenario: Owning rule identifies a deferred skill
- **WHEN** a selected context or trait contains a lightweight scenario rule naming pspec:A
- **THEN** the rule retains its task condition and target reference without making A's procedure part of profile composition or guidance rendering

### Requirement: Profile defaults layer and installations deduplicate

Profiles SHALL provide defaults without copying definitions or runtime answers; explicit project values SHALL override selected-profile defaults, which SHALL override global-profile defaults. Conflicting same-tier defaults, unknown aliases or ambiguous identities SHALL be diagnosed, not chosen by order. Repeated installations SHALL deduplicate by identity, agent, scope and project root without collapsing distinct scopes, and excluding a profile SHALL NOT uninstall shared user-level skills.

#### Scenario: Same-precedence defaults conflict
- **WHEN** two selected-tier profiles supply different defaults for one variable
- **THEN** composition reports a conflict instead of picking one by order

#### Scenario: Distinct scopes are kept
- **WHEN** one skill is selected at user scope and at project scope
- **THEN** both installation targets remain

### Requirement: Python CLI profile supplies tooling defaults and guidance

The Python CLI profile SHALL supply the overridable defaults language = "python", cli_framework = "typer", build_tool = "uv", test_runner = "pytest" and test_command = "uv run pytest", and its context SHALL declare typed inputs with matching fallbacks. utility_path SHALL come from configuration or a profile, not an assumed package name. Guidance SHALL cover CLI contracts, thin handlers, utility responsibilities and proportional verification, keeping the TDD procedure out of compiled context.

#### Scenario: No assumed utility path
- **WHEN** neither configuration nor a profile supplies utility_path
- **THEN** the context does not invent a package-based location

#### Scenario: TDD reference covers behavior work only
- **WHEN** the session is documentation, investigation or environment-only work
- **THEN** the compiled TDD reference does not apply to it

### Requirement: Python CLI profile includes utility planning

The Python CLI profile SHALL reference @builtin/utils-planning-aware through its profiles list, so the bundle includes utility planning and utility-before-wiring guidance and the pspec-plan-utilities skill, with a single same-target pspec-tdd contribution when both profiles reference it.

#### Scenario: Bundle includes utility planning
- **WHEN** the Python CLI profile is composed
- **THEN** the bundle contains the utility planning guidance and the pspec-plan-utilities skill

#### Scenario: TDD is contributed once
- **WHEN** both the Python CLI and utility planning profiles reference pspec-tdd for the same target
- **THEN** the bundle holds one pspec-tdd contribution

### Requirement: Resource shapes are validated by kind

Contexts SHALL reject hooks and a top-level runtime body or when, and traits SHALL reject attach destinations and compiletime inputs. Mixed shapes and legacy config/hook mode declarations SHALL produce migration diagnostics rather than silently changing ownership, and profiles SHALL NOT own attachment destinations or hook selectors.

#### Scenario: Context with hooks is rejected
- **WHEN** a context resource declares hooks
- **THEN** catalog loading reports a migration diagnostic

#### Scenario: Profile cannot set destinations
- **WHEN** a profile tries to declare an attachment destination or hook selector
- **THEN** it is rejected

### Requirement: Conditions are trusted executable rules

Conditions SHALL be documented as trusted executable rules with host capabilities, not isolated untrusted code; fresh bindings SHALL NOT be described as deep isolation, filesystem confinement, complete time limits or rollback of callback effects. Evaluation SHALL NOT prompt for skill inputs or substitute stored values for capability results, and evaluation plumbing SHALL NOT persist results, install assets or prompt.

#### Scenario: Stored values never replace probes
- **WHEN** a condition calls a capability
- **THEN** it receives the actual result rather than a stored value

#### Scenario: Documentation states the trust model
- **WHEN** a user reads condition documentation
- **THEN** it describes conditions as trusted rules without isolation guarantees

### Requirement: Condition outcomes affect only their contribution

False SHALL omit only its contribution, keeping other guidance, skills and native registrations. Context publication and configuration or expression authoring errors SHALL stay atomic with no successful partial result, while runtime hook delivery MAY isolate an operational command-probe failure to its owning optional trait when it reports the diagnostic and keeps independently resolved traits.

#### Scenario: Authoring error fails the whole sync
- **WHEN** one context condition has a syntax error
- **THEN** sync publishes no partial result

#### Scenario: Isolated probe failure is still reported
- **WHEN** hook delivery isolates a failed command probe to its trait
- **THEN** the diagnostic is reported and other resolved traits are delivered

### Requirement: Installation scope does not govern runtime selection

Scope SHALL govern installation only, not runtime selection between installed copies, where native agent precedence SHALL stay authoritative. User/project coexistence SHALL NOT be a Powerspec conflict or require a scope prompt, and scope SHALL NOT relocate context destinations or generic hook dispatchers.

#### Scenario: Coexisting copies need no prompt
- **WHEN** a skill is installed at both user and project scope
- **THEN** Powerspec neither reports a conflict nor asks which scope to use

#### Scenario: Scope does not move hooks
- **WHEN** a profile declares project scope
- **THEN** context destinations and the generic hook dispatchers stay where they are

### Requirement: Subprofile defaults follow how they are reached

Profiles reached through the explicitly selected root SHALL supply selected-tier defaults, and those reached only through automatic globals SHALL supply global-tier defaults; an identity reached both ways SHALL contribute once at the selected tier. Parent/child depth and declaration order SHALL NOT add a precedence layer, and unequal values at one tier SHALL use the existing conflict diagnostic.

#### Scenario: Global-only subprofile supplies global defaults
- **WHEN** a subprofile is reachable only through an automatic global profile
- **THEN** its defaults apply at the global tier

#### Scenario: Declaration order adds no precedence
- **WHEN** two profiles at one tier are declared in different orders
- **THEN** their defaults keep the same tier and conflicting values are diagnosed

### Requirement: Profile exclusions apply before expansion

The consumer's and explicitly selected root's exclude-profiles SHALL apply before contributions expand, and excluding the selected root SHALL conflict. Excluding a nested profile SHALL omit it and descendants reachable only through it, keeping descendants reachable another way. Subprofiles and automatic globals SHALL add no exclusion layer, their exclude-profiles applying only as a selected root, and no reference or automatic mount SHALL restore an excluded identity.

#### Scenario: Excluding the selected root conflicts
- **WHEN** exclude-profiles names the explicitly selected root
- **THEN** composition reports a conflict

#### Scenario: Excluded identity stays excluded
- **WHEN** an excluded profile is referenced again elsewhere or is global
- **THEN** it is not restored

### Requirement: Utility guidance defines portable helpers

The guidance SHALL define utilities as generic helpers usable by other projects through portable inputs and outputs, with a concrete outside use and domain-neutral verification. Application models, profile/configuration policy and workflow rules SHALL stay with callers, and internal reuse alone SHALL NOT make a service a utility. It SHALL reuse suitable utilities, avoid artificial utility work, and exclude environment, documentation and configuration work without behavioral effects.

#### Scenario: Existing utility is reused
- **WHEN** a suitable utility already exists
- **THEN** the guidance directs reuse instead of a new helper

#### Scenario: Internal reuse is not a utility
- **WHEN** an application service is reused only inside the current project
- **THEN** it is not classified as a utility

### Requirement: Utility guidance stays within its authority

Utility planning SHALL NOT authorize implementation, and utility verification SHALL NOT claim application integration is complete. These contexts SHALL reuse existing destinations without a schema artifact or embedded skill procedures, and foundation composition SHALL keep this source guidance without executing it or publishing config.yaml.

#### Scenario: Planning does not start implementation
- **WHEN** utility planning guidance applies
- **THEN** it does not authorize implementing the planned helper

#### Scenario: No schema artifact is added
- **WHEN** the utility contexts are composed
- **THEN** they use existing destinations without adding a schema artifact

### Requirement: Armed queries read a fixed snapshot

The membership snapshot SHALL be computed before evaluation and SHALL NOT depend on event match, condition results, compilation, installation, resolution or execution. Queries SHALL NOT evaluate resources, mutate selection, remove assets or recurse. Contexts SHALL use their sync-time snapshot and traits their invocation's. Variables SHALL NOT shadow armed, invalid queries SHALL be diagnosed, and failed composition SHALL be an error, not false.

#### Scenario: Variable named armed
- **WHEN** a runtime variable is named armed
- **THEN** conditions still receive the armed capability

#### Scenario: Invalid query is diagnosed
- **WHEN** armed receives an invalid kind, a malformed, unqualified or wildcard reference, or a non-string argument
- **THEN** evaluation reports a diagnostic

#### Scenario: Composition failure is an error
- **WHEN** the effective bundle cannot be composed
- **THEN** armed queries report an error instead of returning false

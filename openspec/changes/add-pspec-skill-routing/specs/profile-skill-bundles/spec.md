# Spec Delta

## MODIFIED Requirements

### Requirement: Profiles reference resources and supply defaults

Profiles SHALL reference contexts and traits through separate optional lists of qualified resource-reference strings. The optional skills and resolve-skills lists SHALL use qualified resource references for packaged or registered catalog resources and `<source-alias>/<path-pattern>` strings for direct paths in a declared Git source. skills SHALL select resources for native installation and explicit Powerspec resolution. resolve-skills SHALL select resources for explicit Powerspec resolution without creating native installation targets. Both lists SHALL participate in the same effective profile graph after exclusions, retain source provenance, and require matching source declarations for direct Git selections. Profiles SHALL provide defaults without copying resource definitions or runtime answers. Explicit project values SHALL override selected-profile defaults, which SHALL override global-profile defaults. Conflicting same-precedence defaults, unknown source aliases, or ambiguous resource identities SHALL be diagnosed rather than silently selected by traversal order. Repeated skill installations SHALL be deduplicated by resolved identity, target agent, scope, and project root where applicable. Distinct installation scopes SHALL NOT be collapsed. Excluding a profile SHALL not uninstall shared user-level skills as a side effect.

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


### Requirement: One profile declares one skill installation scope

A profile SHALL declare a single top-level scope of user or project applying to every installation target it declares through skills. resolve-skills entries SHALL have no installation scope or destination and SHALL NOT require a project root solely because the profile declares project scope. Omitted scope SHALL default to user. Skill references SHALL remain strings; per-skill scope overrides SHALL NOT be supported. Invalid scope values SHALL be diagnosed rather than inferred. Composing profiles SHALL preserve the declaring profile's scope for each installation contribution, including global profiles. The global flag SHALL govern mounting independently of installation scope. Scope SHALL govern installation only, not runtime selection between installed copies. Native agent precedence SHALL remain authoritative. User/project coexistence SHALL NOT itself constitute a Powerspec conflict or require a scope-choice prompt. Scope SHALL NOT relocate context destinations or generic hook dispatchers.

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


### Requirement: Conditions can query selected resources

Conditions SHALL expose armed(kind, reference) returning a Boolean for membership in the invoking consumer's effective bundle after composition, exclusions, and deduplication. Supported kinds SHALL be skill, trait, context, and profile, with distinct identity namespaces. Queries SHALL use exact qualified resource identities under the existing identity contract; skill identities SHALL respect declared skill names and resolved remote contributions SHALL be queryable by their concrete source-relative identities. Retained global/subprofiles SHALL count as selected. Skill membership SHALL include selections from both skills and resolve-skills without treating selection as proof of native availability. An exact valid identity absent from the bundle SHALL return false without loading/acquiring sources or inspecting installations.

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

#### Scenario: Resolve-only membership
- **WHEN** a retained profile selects an exact resource only through resolve-skills
- **THEN** armed reports that skill as selected without probing or creating an installation


## ADDED Requirements

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

# Spec Delta

## MODIFIED Requirements

### Requirement: Skill lookup is read-only and project-aware

Native --path resolution SHALL read the skill root explicitly supplied by the caller without discovering native installations, enumerating same-named copies, validating membership in an agent installation directory, installing, updating, or executing skills, writing variable files, or editing OpenSpec configuration. The supplied location SHALL identify an existing skill directory, its SKILL.md, or its pspec.toml. The selected location SHALL remain authoritative even when the catalog or another installed copy contains a different revision or classification. Invalid locations SHALL produce diagnostics without fallback to a same-named resource. Manifest-relative references SHALL retain their existing containment and selected-resource validation.

Available project values SHALL come from the invoking project's nearest applicable consumer inside its Git boundary, not from the supplied skill directory or authoring repository. The caller SHALL retain its task working directory while passing the skill location. A malformed nearest configuration SHALL be diagnosed rather than ignored in favor of another project. An invocation without project configuration SHALL use skill defaults where sufficient and report any required missing project inputs without inventing a project boundary. Agent identity SHALL supply invocation context only; it SHALL NOT determine which skill copy is read. Skill resolution SHALL NOT acquire or refresh remote sources to resolve the supplied content. The explicit --ref route SHALL instead select a resource from the owning consumer's effective profile selections; it SHALL preserve the same read-only installation and input boundaries without substituting catalog content for a native --path invocation.

#### Scenario: Same user-level skill in two repositories
- **WHEN** two projects supply the same skill path with different local variables
- **THEN** each receives its own selected content without changing the shared skill

#### Scenario: Missing project inputs
- **WHEN** a supported skill is invoked outside a configured project and requires project-specific values
- **THEN** resolution reports those missing inputs without reading a sibling repository or writing a guessed configuration

#### Scenario: User and project copies coexist
- **WHEN** user and project copies share a name and the agent supplies one selected path
- **THEN** resolution reads that path without inspecting the other copy or reporting coexistence ambiguity

#### Scenario: Native integration selects another skill location
- **WHEN** the agent supplies a valid skill directory outside known user and project installation roots
- **THEN** Powerspec resolves its manifest without requiring installation registration or using ZuAT to validate native selection

#### Scenario: Invalid explicit location
- **WHEN** the supplied location is missing, is an unrelated file, or cannot be read
- **THEN** resolution fails with a located diagnostic and does not search the catalog or native installations for a replacement

#### Scenario: Runtime manifest differs from published guidance
- **WHEN** generated guidance described a catalog skill as dynamic but the agent selected a different version
- **THEN** the explicit path's current manifest or absence of one determines the resolution outcome without replacing the agent's selection

#### Scenario: Remote source service is unavailable
- **WHEN** an explicitly supplied local skill is readable but an unrelated selected remote source cannot be reached
- **THEN** content resolution still uses the supplied local skill and available profile values without acquiring that source

## ADDED Requirements

### Requirement: Catalog resolution returns selected procedures without provisioning

Catalog resolution SHALL use effective skills and resolve-skills, deduplicate identities and reject ambiguous names or incomplete evidence. Exact requests SHALL inspect only necessary membership evidence. Valid manifests SHALL use existing assembly/input contracts; ordinary skills SHALL return frontmatter-stripped entrypoints. Failures SHALL NOT become ordinary fallback. Lookup SHALL NOT provision or execute skills, write answers, acquire sources or repair state.

#### Scenario: Installation and resolution declarations overlap
- **WHEN** several retained profiles select the same resource through both lists
- **THEN** bare-name matching counts one resource identity and dynamic inputs resolve once

#### Scenario: Native copy differs from catalog content
- **WHEN** the task requests pspec:helper and the selected catalog and a native-installed helper differ
- **THEN** the explicit catalog route uses its catalog resource while a separate native --path request remains authoritative for that selected path

#### Scenario: Source evidence is incomplete
- **WHEN** a bare-name search cannot inspect one selected remote selector
- **THEN** resolution reports incomplete selection evidence without claiming another candidate is unique or installing a replacement

#### Scenario: Exact local selection tolerates an unrelated unavailable source
- **WHEN** an exact selected local reference can be established but another selected remote source is unavailable
- **THEN** the exact local reference resolves without acquiring or requiring that unrelated source

#### Scenario: Missing remote materialization
- **WHEN** the requested resource's selected remote source has not been prepared
- **THEN** resolution fails with an actionable source diagnostic and performs no initialization or acquisition

#### Scenario: Invalid catalog manifest
- **WHEN** a selected skill has an unreadable, malformed, or escaping pspec.toml
- **THEN** catalog resolution fails without returning an ordinary fallback or partial procedure

#### Scenario: Preserve dynamic assembly safety
- **WHEN** a catalog skill declares a manifest
- **THEN** resolution preserves existing dynamic assembly, required-input, pending and containment contracts
- **AND** unreadable, malformed or escaping manifests fail without ordinary fallback

#### Scenario: Lookup stays read-only
- **WHEN** a selected catalog procedure is requested
- **THEN** resolution performs no native installation, adoption, execution, update or removal, writes no answers and runs no acquisition or repair fallback
- **AND** unavailable source content produces a source-specific diagnostic directing explicit preparation or upgrade as appropriate

### Requirement: Catalog results retain usable source locations

Catalog pending and resolved results SHALL identify a complete canonical skill directory usable after process exit. Content, provenance and supporting resources SHALL agree on that source tree. Resolution SHALL use existing source locations without native installation or persistent extraction caches. Temporary merged or extracted roots SHALL NOT be exposed as durable paths; providers without a durable complete tree SHALL fail explicitly.

#### Scenario: Editable installation merges catalog metadata
- **WHEN** an editable installation combines checkout-authored resources with packaged upstream skills
- **THEN** a resolved authored skill points to its complete checkout directory and a packaged-only skill points to its complete installed directory, both readable after process exit

#### Scenario: Read supporting reference after resolution
- **WHEN** returned instructions refer to references/details.md inside the skill
- **THEN** the caller can read it relative to skill_path after the command exits without installing the skill

#### Scenario: Remote source remains pinned
- **WHEN** a remote selected resource is resolved
- **THEN** its source directory belongs to the consumer's retained selection rather than a moving source claim

#### Scenario: Temporary-only resource provider
- **WHEN** a provider offers only a directory whose lifetime ends with the resolution context
- **THEN** the command fails with a located diagnostic rather than returning that path as usable

#### Scenario: Partial authored tree cannot borrow packaged files
- **WHEN** an authored skill overrides packaged content but lacks required selected files
- **THEN** resolution reports the incomplete source instead of combining incompatible trees or returning a misleading supporting-file root

### Requirement: Procedure retrieval remains limited to the needed skill

Catalog responses SHALL contain only the requested procedure and active additions, or its pending questions without procedure text. Candidate identity inspection SHALL remain internal without emitting sibling procedures, descriptions, inactive branches or unrelated supporting content. Resolution SHALL NOT evaluate sibling procedural inputs or speculative dependencies. Ambiguity diagnostics and explicit status SHALL retain their required identity output.

#### Scenario: Resolve A while other skills remain available
- **WHEN** A, B, and C are selected and the current request needs A
- **THEN** the response contains A's procedure and active additions without B/C procedure bodies or A's inactive branch content

#### Scenario: Unused skill needs configuration
- **WHEN** unrequested B has procedural inputs with no configured answers while A is requested
- **THEN** A's response contains no questions or procedural content for B

#### Scenario: Supporting files are progressive
- **WHEN** returned instructions reference supporting documents or another skill needed only in a later step or scenario
- **THEN** those references do not cause the resolver to return their contents eagerly

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

Explicit catalog resolution SHALL select only resources contributed by the owning consumer's effective skills and resolve-skills entries. Repeated selections of one identity SHALL count once for name matching; distinct identities with the same declared name SHALL require an exact reference. An inability to inspect selected candidates SHALL NOT be treated as evidence of absence or uniqueness. A bare-name lookup with unresolved selected candidates SHALL fail rather than guess. An exact reference SHALL inspect only selection evidence needed to establish that resource's membership and content, without requiring unrelated remote materializations.

A selected skill with a valid manifest SHALL use the existing dynamic assembly, required-input, pending, containment, and error contracts. A selected skill without a manifest SHALL return its ordinary entrypoint procedure with frontmatter removed. Broken or escaping manifests SHALL fail rather than fall back to ordinary content. Resolution SHALL NOT install, adopt, execute, update, or remove native skills, write answers, acquire sources, or run a repair fallback. Unavailable source content SHALL produce a source-specific diagnostic directing explicit preparation or upgrade as appropriate.

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

### Requirement: Catalog results retain usable source locations

Catalog pending and resolved results SHALL identify a canonical source directory usable after the resolver process exits. Relative references, scripts, and assets in the procedure SHALL remain grounded in that selected complete skill directory. Source identity and provenance SHALL match the content returned. Resolver-owned temporary merged or extracted directories SHALL NOT be exposed as durable skill paths. Resolution SHALL use existing source locations rather than installing a native copy or creating a persistent extracted skill cache. A provider that cannot supply a durable complete skill root SHALL report an explicit unsupported-location diagnostic instead of success with a disappearing path.

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

### Requirement: Procedure retrieval remains limited to the needed skill

A catalog request SHALL return only the selected target's procedure and its active dynamic additions. Candidate-identity inspection needed for selection and name disambiguation SHALL remain internal and SHALL NOT emit other candidates' procedure bodies, per-skill discovery descriptions, inactive branches, or unrelated supporting documents into the agent-facing result. The resolver SHALL NOT evaluate unrelated skills' procedural inputs or resolve them as speculative dependencies. Pending results SHALL continue to withhold procedural content. Necessary exact identities in ambiguity diagnostics and explicitly requested status output SHALL remain available under their existing contracts.

#### Scenario: Resolve A while other skills remain available
- **WHEN** A, B, and C are selected and the current request needs A
- **THEN** the response contains A's procedure and active additions without B/C procedure bodies or A's inactive branch content

#### Scenario: Unused skill needs configuration
- **WHEN** unrequested B has procedural inputs with no configured answers while A is requested
- **THEN** A's response contains no questions or procedural content for B

#### Scenario: Supporting files are progressive
- **WHEN** returned instructions reference supporting documents or another skill needed only in a later step or scenario
- **THEN** those references do not cause the resolver to return their contents eagerly

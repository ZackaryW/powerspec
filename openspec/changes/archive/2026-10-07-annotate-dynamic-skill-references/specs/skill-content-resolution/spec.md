# Spec Delta

## MODIFIED Requirements

### Requirement: Skill support is described by pspec.toml

A supported skill SHALL carry pspec.toml alongside its entrypoint and referenced resources. SKILL.md SHALL own the shared procedure and its static order. Manifest version 2 SHALL declare inputs, defaults, and dynamic additions through `[[dynamic]]` entries: `section` identifies an exact destination heading in the entrypoint, `pos` SHALL be `after` or `replace`, `path` identifies a skill-relative resource with optional declared variable substitution, and optional `source_section` identifies an exact heading in that source. An omitted `source_section` SHALL select the complete source file. Each input SHALL declare zero or one prompt parser. `before`, `combine`, hint groups, `default_hint`, multiple parsers, numbered insertion, and other position values SHALL produce migration diagnostics rather than being silently reinterpreted. References SHALL resolve relative to the explicitly supplied skill root rather than the working directory. A valid manifest SHALL establish dynamic-resolution support independently of the number of inputs or dynamic entries and independently of current branch activation.

Bundled manifest-backed skill entrypoints SHALL provide concise instructions for requesting Powerspec content assembly after native selection, including direct invocation without generated context or a matching trait. Those instructions SHALL distinguish an unresolved entrypoint from content already returned by Powerspec and SHALL NOT cause an already-resolved document to recursively request itself.

#### Scenario: Skill installed from a bundle
- **WHEN** a supported version 2 skill is copied to the selected agent's installation
- **THEN** its pspec.toml and referenced content remain usable without the authoring checkout

#### Scenario: No workflow trait
- **WHEN** the agent selects a bundled dynamic skill through its native integration without a matching trait or compiled guidance
- **THEN** the entrypoint explains the explicit-location content handoff and the selected manifest can be resolved directly

#### Scenario: Version 1 manifest requires migration
- **WHEN** resolution encounters a version 1 manifest or a removed version 1 field
- **THEN** it reports a migration diagnostic without returning partially resolved content

#### Scenario: More than one prompt parser
- **WHEN** an input declares multiple prompt parsers
- **THEN** manifest validation rejects the ambiguous input instead of selecting the first parser

#### Scenario: Returned content is already assembled
- **WHEN** the agent receives the resolved shared procedure and selected additions
- **THEN** the entrypoint instructions direct it to follow that result without requesting the same assembly again

### Requirement: Skill lookup is read-only and project-aware

Resolution SHALL read the skill root explicitly supplied by the caller without discovering native installations, enumerating same-named copies, validating membership in an agent installation directory, installing, updating, or executing skills, writing variable files, or editing OpenSpec configuration. The supplied location SHALL identify an existing skill directory, its SKILL.md, or its pspec.toml. The selected location SHALL remain authoritative even when the catalog or another installed copy contains a different revision or classification. Invalid locations SHALL produce diagnostics without fallback to a same-named resource. Manifest-relative references SHALL retain their existing containment and selected-resource validation.

Available project values SHALL come from the invoking project's nearest applicable consumer inside its Git boundary, not from the supplied skill directory or authoring repository. The caller SHALL retain its task working directory while passing the skill location. A malformed nearest configuration SHALL be diagnosed rather than ignored in favor of another project. An invocation without project configuration SHALL use skill defaults where sufficient and report any required missing project inputs without inventing a project boundary. Agent identity SHALL supply invocation context only; it SHALL NOT determine which skill copy is read. Skill resolution SHALL NOT acquire or refresh remote sources to resolve the supplied content.

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

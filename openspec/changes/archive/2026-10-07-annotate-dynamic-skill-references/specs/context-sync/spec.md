# Spec Delta

## MODIFIED Requirements

### Requirement: Context compilation uses noninteractive shared inputs

Context compilation SHALL use persistent config.toml shared variables, selected-profile defaults, global-profile defaults, then context declaration defaults. It SHALL NOT consume current.toml, change-specific values, or runtime prompts. Invalid explicit and missing required values SHALL produce diagnostics without fallback from invalid values. Declared variable placeholders SHALL be substituted once; unrelated angle-bracket prose SHALL remain literal. Explicit `<skill:name>` references SHALL be rendered as their declared names from the selected validated catalog without requiring native installation or embedding skill procedures. Unknown declared references SHALL fail rather than be silently omitted.

For each emitted attachment, compilation SHALL classify its explicit skill references from the referenced catalog resources. A valid `pspec.toml` SHALL classify the skill as requiring dynamic resolution, including a manifest containing only inputs or currently inactive additions. An absent manifest SHALL classify that resource as ordinary. An unreadable or malformed existing manifest, or conflicting classification among selected resources sharing the referenced name, SHALL produce a located compilation error rather than assume an ordinary skill or choose native installation precedence. Classification SHALL NOT resolve runtime values, select dynamic branches, read branch content, prompt, or execute a skill. Text introduced by variable substitution SHALL NOT become a new skill reference. Unmentioned skills SHALL NOT acquire headings or cause classification-only manifest validation.

#### Scenario: Reviewed tooling defaults
- **WHEN** the Python CLI context compiles with the profile defaults and an explicit utility_path
- **THEN** its guidance identifies uv, pytest, uv run pytest, and the configured utility location without a prompt or tool installation

#### Scenario: Temporal override does not compile
- **WHEN** current.toml or a change table supplies another test_command
- **THEN** sync still uses shared persistent/default values and leaves those runtime files unchanged

#### Scenario: Skill reference is available as a resource
- **WHEN** an attachment references pspec-tdd from a validated catalog
- **THEN** its published guidance names that skill and identifies its dynamic-resolution requirement from the manifest without executing or embedding its procedure

#### Scenario: Broken temporal file does not affect compilation
- **WHEN** shared persistent context inputs are valid but current.toml contains malformed runtime state
- **THEN** sync compiles without reading that temporal file, preserving it for separate runtime diagnosis

#### Scenario: Input-only manifest
- **WHEN** a mentioned skill has a valid manifest with inputs and no dynamic additions
- **THEN** it is classified as requiring dynamic resolution without requesting those inputs during sync

#### Scenario: All dynamic branches are currently inactive
- **WHEN** a mentioned skill has a valid manifest whose additions would be inactive under current runtime values
- **THEN** it remains classified as requiring dynamic resolution without consulting those runtime values

#### Scenario: Ordinary skill
- **WHEN** a referenced catalog skill has no pspec.toml
- **THEN** its ordinary name is rendered without a requirement to call Powerspec or obtain a null result

#### Scenario: Malformed referenced manifest
- **WHEN** a referenced resource has an unreadable or invalid pspec.toml
- **THEN** sync identifies the resource and fails before publishing any change to config.yaml

#### Scenario: Literal text is not a new reference
- **WHEN** variable substitution introduces text resembling `<skill:name>` or prose contains a bare skill name
- **THEN** that text is not recursively classified or used to add a dynamic-resolution heading

## ADDED Requirements

### Requirement: Dynamic-resolution reminders accompany their owning guidance blocks

Each emitted context attachment that mentions one or more manifest-backed skills SHALL begin with a Markdown section heading identifying those skills as requiring dynamic resolution. The heading and concise following instructions SHALL be inside that attachment's generated text, within the existing context scalar or rules/operation guidance item; they SHALL NOT introduce new YAML schema keys or a global skill inventory. Names SHALL be deduplicated in first-mention order within the attachment, and ordinary referenced skills SHALL NOT be listed as dynamic. Multiple attachments SHALL each retain their own applicable reminder.

The instructions SHALL direct the agent to select the skill through its native integration and supply that selected skill's location to Powerspec before following its dynamic procedure. They SHALL explain that the reminder applies when the skill is invoked under the attachment's existing task conditions; publication SHALL NOT activate a workflow. Generated configuration SHALL NOT embed authoring-source paths as native-selected locations. The remaining authored body and existing per-attachment provenance SHALL remain intact. Attachments containing only ordinary skills or no skill references SHALL receive no dynamic-resolution heading.

The reminder SHALL be managed as part of its owning contribution. A later sync SHALL remove or update it when mentions, classification, or attachment eligibility change. Repeated sync with identical inputs SHALL remain byte-idempotent and preserve handwritten guidance and unrelated YAML.

#### Scenario: Mixed and repeated mentions
- **WHEN** an emitted attachment mentions dynamic skill A, ordinary skill B, A again, and dynamic skill C
- **THEN** its section heading lists A and C once in that order, followed by native-selection and dynamic-resolution instructions and the authored body
- **AND** B retains an ordinary mention without a Powerspec prerequisite

#### Scenario: All supported destinations
- **WHEN** eligible attachments with dynamic skill references target context, rules.design, and operations.apply.guidance
- **THEN** each generated text block contains its own heading without changing the target YAML schema or attachment identifier

#### Scenario: Ineligible attachment
- **WHEN** an attachment's condition evaluates false
- **THEN** neither its body nor its dynamic-resolution heading is emitted

#### Scenario: Dynamic mention removed
- **WHEN** a later sync removes the final dynamic mention or the referenced resource no longer has a manifest
- **THEN** the former heading and reminder disappear while the current body and user-authored content are preserved

#### Scenario: Repeat publication
- **WHEN** the same guidance, references, and manifests are synchronized twice
- **THEN** the second sync reports unchanged and does not duplicate headings or reminders

#### Scenario: Skill is selected but unmentioned
- **WHEN** the bundle selects a dynamic skill but no emitted attachment explicitly references it
- **THEN** sync does not add a heading or a separate invocation instruction for that skill

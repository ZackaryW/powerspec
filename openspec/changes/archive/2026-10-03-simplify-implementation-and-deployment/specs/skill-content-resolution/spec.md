# Spec Delta

## MODIFIED Requirements

### Requirement: Skill support is described by pspec.toml

A supported installed skill SHALL carry pspec.toml alongside its entrypoint and referenced resources. SKILL.md SHALL own the shared procedure and its static order. Manifest version 2 SHALL declare inputs, defaults, and dynamic additions through `[[dynamic]]` entries: `section` identifies an exact destination heading in the entrypoint, `pos` SHALL be `after` or `replace`, `path` identifies a skill-relative resource with optional declared variable substitution, and optional `source_section` identifies an exact heading in that source. An omitted `source_section` SHALL select the complete source file. Each input SHALL declare zero or one prompt parser. `before`, `combine`, hint groups, `default_hint`, multiple parsers, numbered insertion, and other position values SHALL produce migration diagnostics rather than being silently reinterpreted. References SHALL resolve relative to the installed skill root rather than the working directory.

#### Scenario: Skill installed from a bundle
- **WHEN** a supported version 2 skill is copied to the selected agent's installation
- **THEN** its pspec.toml and referenced content remain usable without the authoring checkout

#### Scenario: No workflow trait
- **WHEN** a supported skill is available through a selected profile without a matching workflow trait
- **THEN** direct lookup still resolves its manifest and returns the selected procedure

#### Scenario: Version 1 manifest requires migration
- **WHEN** lookup encounters a version 1 manifest or a removed version 1 field
- **THEN** it reports a migration diagnostic without returning partially resolved content

#### Scenario: More than one prompt parser
- **WHEN** an input declares multiple prompt parsers
- **THEN** manifest validation rejects the ambiguous input instead of selecting the first parser

### Requirement: Resolve only the invoked skill's necessary inputs

Lookup SHALL combine the requested skill's defaults with mounted profile defaults and explicit project or temporal values when available. Explicit values SHALL take precedence over prompt suggestions. Inputs SHALL be evaluated only when required to select or render a reachable part of this skill; excluded branches and unrelated skills SHALL not request inputs. Missing values needed by a decision SHALL remain pending, while invalid values or dependency cycles SHALL produce diagnostics. Conversation interpretation and answers SHALL belong to the agent rather than a hidden classifier inside the resolver.

Lookup SHALL consume the shared/change layers and precedence defined by consumer-configuration, applying this skill's value defaults last. A valid effective value SHALL bypass its prompt. A prompt default SHALL remain a suggestion, distinct from a value default. Invalid effective values SHALL produce diagnostics without silently substituting lower-precedence values or prompting for replacement. Resolution SHALL NOT probe repository files to infer prompt suggestions.

#### Scenario: Persistent language skips its prompt
- **WHEN** config.toml declares `language = "python"` under `[vars]` and current.toml has no override
- **THEN** lookup substitutes python into the selected path and does not activate the language prompt

#### Scenario: Temporal language overrides persistent language
- **WHEN** current.toml supplies a valid different language value for the same skill
- **THEN** lookup uses that value without prompting or modifying persistent configuration

#### Scenario: Skill value default skips its prompt
- **WHEN** no stronger value exists and the skill declares a valid input value default
- **THEN** lookup uses that value without treating a prompt default as an answer

#### Scenario: Prompt default remains unconfirmed
- **WHEN** an unresolved input has a prompt default and no effective value
- **THEN** lookup returns that value only as a suggestion and leaves the input pending

#### Scenario: Python TDD does not ask about BDD
- **WHEN** the Python CLI bundle's TDD skill is invoked
- **THEN** resolution returns its relevant inputs and content without requesting a BDD framework

#### Scenario: Branch is excluded
- **WHEN** a known input value excludes a branch
- **THEN** inputs used only by that branch are not requested and its content is omitted

#### Scenario: A required choice is missing
- **WHEN** a reachable branch depends on an unanswered input
- **THEN** lookup reports the pending choice without guessing or reading an unrelated branch

#### Scenario: Invalid configured input
- **WHEN** an effective configured value has the wrong type or violates its choices
- **THEN** lookup reports the invalid origin without prompting for a replacement or falling back

### Requirement: Return selected content directly and deterministically

For `pos = "after"`, resolution SHALL preserve the shared entrypoint's body and order and insert each selected addition after its named destination section body and descendants, before the next heading of equal or higher rank or at document end. Identical resolved destination/file/source-section contributions SHALL appear once at their first occurrence, and different additions at one destination SHALL follow manifest order. For `pos = "replace"`, the last active declaration for one destination SHALL replace that entire original section, including its heading and descendants, while preserving surrounding sections. Destination and source selectors SHALL each identify an exact unique ATX Markdown heading; headings inside code fences SHALL not count. Output SHALL contain the actual shared and selected text with concise provenance. Declared variable substitution in resource paths or content SHALL occur once without executing code or recursively interpreting inserted content.

#### Scenario: Python additions preserve the shared TDD flow
- **WHEN** Python dynamic entries select scope, red, and green source sections with `pos = "after"`
- **THEN** each addition appears after its named target while the remaining shared flow retains its order

#### Scenario: Shared section is referenced twice
- **WHEN** two active after entries reference the same source section at the same destination
- **THEN** that contribution appears once at its first declaration position

#### Scenario: Several additions share a destination
- **WHEN** two different active after entries target one destination
- **THEN** their content follows manifest order before the next peer or ancestor heading

#### Scenario: Section selection
- **WHEN** a dynamic entry selects one source section from a multi-section resource
- **THEN** output includes that heading and its descendants without unrelated sibling sections

#### Scenario: Last active replacement wins
- **WHEN** several active replace entries target one section
- **THEN** only the final active declaration supplies that section's replacement

#### Scenario: Inactive replacement cannot override
- **WHEN** a later replacement is excluded by its condition
- **THEN** the prior active replacement remains selected

#### Scenario: Duplicate addition
- **WHEN** the same after contribution is selected repeatedly for one destination
- **THEN** it appears once at its first declaration position

### Requirement: Ancestor replacement takes precedence over descendant placements

Resolution SHALL derive destination boundaries and section ancestry from the original entrypoint. An active replacement targeting an ancestor section SHALL suppress active after placements and replacements targeting its descendant sections regardless of declaration order. Resolution SHALL NOT search replacement content for suppressed descendant anchors or replay descendant edits against inserted text. An inactive ancestor replacement SHALL NOT suppress descendant placements.

#### Scenario: Parent replacement suppresses a later child edit
- **WHEN** an active replacement targets a parent section and an active after entry targets its child section
- **THEN** the parent replacement is emitted without the child addition regardless of declaration order

#### Scenario: Parent combination suppresses child placements
- **WHEN** a removed version 1 combine declaration and descendant placements occur in one manifest
- **THEN** version validation rejects the manifest before either operation is applied

#### Scenario: Inactive parent replacement
- **WHEN** the parent replacement is inactive and a child after entry is active
- **THEN** the child addition remains eligible

#### Scenario: Replacement contains a matching child heading
- **WHEN** selected parent replacement content contains a heading matching an original child destination
- **THEN** a suppressed child entry is not reapplied to inserted content

#### Scenario: Placements surround their own target replacement
- **WHEN** active replace and after entries target the same section
- **THEN** the final replacement is followed by the after contribution without restoring the original section

## REMOVED Requirements

### Requirement: Ordered hints suggest rather than select

**Reason**: No bundled skill uses repository-file hints, and retaining dormant inference machinery expands the manifest and filesystem behavior without a current product need.

**Migration**: Supply explicit defaults through the skill or profile, persist accepted values in consumer configuration, or let the single prompt parser request an unresolved choice.

### Requirement: Same-target replacement supports last-wins and combine

**Reason**: Bundled skills require deterministic last-active replacement but do not use accumulator-style combination; retaining combine creates unused ordering and deduplication rules.

**Migration**: Precompose combined source content into one resource and select it with a final `pos = "replace"` entry.

## RENAMED Requirements

- FROM: `### Requirement: Replace substitutes the entire destination section`
- TO: `### Requirement: Replacement substitutes the entire destination section`

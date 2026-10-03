# Skill Content Resolution Specification

## Purpose

Resolve a supported installed skill into the content and inputs needed for its current invocation, preserving shared flow and deterministic dynamic placements.

## Requirements

### Requirement: Skill support is described by pspec.toml

A supported installed skill SHALL carry pspec.toml alongside its entrypoint and referenced resources. SKILL.md SHALL own the shared procedure and its static order. The manifest SHALL declare inputs, defaults, and dynamic additions through [[dynamic]] entries: section identifies a destination heading in the entrypoint, pos declares placement relative to that section and SHALL be before, after, replace, or combine, path identifies a skill-relative resource with optional declared variable substitution, and optional source_section identifies a heading in that source. An omitted source_section SHALL select the complete source file. The reviewed TDD entries SHALL explicitly use pos = "after". The old after key SHALL NOT identify destinations in this shape. Numbered insert placement is outside this change; unsupported pos values SHALL produce a manifest diagnostic. The manifest SHALL NOT require enumerating shared content or duplicating the static procedure, and the entrypoint SHALL NOT require inline insertion markers. References SHALL resolve relative to the installed skill root rather than the working directory. Source and installed forms SHALL preserve equivalent behavior without a matching always-selected trait.

#### Scenario: Skill installed from a bundle
- **WHEN** the supported skill is copied to the selected agent's user-level installation
- **THEN** its pspec.toml and referenced content remain usable without the authoring checkout

#### Scenario: No workflow trait
- **WHEN** TDD is available as a profile skill without a TDD trait selected for OpenSpec
- **THEN** direct lookup can still resolve its manifest and return the selected TDD procedure

### Requirement: Resolve only the invoked skill's necessary inputs

Lookup SHALL combine the requested skill's defaults with mounted profile defaults and explicit project or temporal values when available. Explicit values SHALL take precedence over suggestions. Inputs SHALL be evaluated only when required to select or render a reachable part of this skill; excluded branches and unrelated skills SHALL not request inputs. Missing values needed by a decision SHALL remain pending, while invalid values or dependency cycles SHALL produce diagnostics. Conversation interpretation and answers SHALL belong to the agent rather than a hidden classifier inside the resolver.

Lookup SHALL consume the shared/change layers and precedence defined by consumer-configuration, applying this skill's value defaults last. A valid effective value SHALL bypass its prompt and hint evaluation. Prompt defaults and hints SHALL remain suggestions, distinct from value defaults. Invalid effective values SHALL produce diagnostics without silently substituting lower-precedence values or prompting for replacement.

#### Scenario: Persistent language skips its prompt
- **WHEN** config.toml declares language = "python" under [vars] and current.toml has no override
- **THEN** lookup substitutes python into languages/<language>.md and does not activate the language prompt

#### Scenario: Temporal language overrides persistent language
- **WHEN** current.toml supplies a valid different language value for the same skill
- **THEN** lookup uses that value without prompting or modifying the persistent configuration

#### Scenario: Skill value default skips its prompt
- **WHEN** no stronger value exists and the skill declares a valid input value default
- **THEN** lookup uses that value without treating the prompt's suggested default as an answer

#### Scenario: Invalid configured input
- **WHEN** the effective configured language has an invalid type or violates its declared allowed values
- **THEN** lookup reports an input diagnostic without activating a replacement prompt or falling back to a default

#### Scenario: Python TDD does not ask about BDD
- **WHEN** the Python CLI bundle's TDD skill is invoked
- **THEN** resolution returns its relevant inputs and content without requesting a BDD framework

#### Scenario: Branch is excluded
- **WHEN** a known language choice excludes a framework-specific branch
- **THEN** inputs used only by that branch are not requested and its content is omitted

#### Scenario: A required choice is missing
- **WHEN** a branch condition depends on an unanswered input
- **THEN** the result identifies the decision and leaves its dependent content pending without guessing

### Requirement: Ordered hints suggest rather than select

Manifests SHALL support repeated hint IDs forming local groups in authored order. A prompt parser SHALL reference one group through scalar default_hint. The first matching hint SHALL supply the suggested default; no match SHALL retain the prompt's ordinary default or no suggestion. Explicit configured values SHALL skip hint-driven prompting. Hints SHALL use typed, read-only detectors and SHALL neither persist values nor count as confirmed answers. Hint lookup SHALL not merge groups across skills.

#### Scenario: More than one detector matches
- **WHEN** two hints with the same ID match
- **THEN** only the first authored match supplies the suggestion and the agent still obtains an answer

#### Scenario: Explicit selection exists
- **WHEN** a configured value differs from a matching hint
- **THEN** the configured value wins without an unnecessary prompt

#### Scenario: No hint matches
- **WHEN** the group produces no match
- **THEN** the prompt uses its ordinary default if declared, otherwise requests a choice without a suggestion

### Requirement: Return selected content directly and deterministically

For pos = "before", resolution SHALL place selected source content immediately before the destination heading while preserving the target section. For pos = "after", resolution SHALL preserve the shared entrypoint's body and order, inserting each selected dynamic addition after its named destination section's body and descendants, before the next heading of equal or higher rank, or at document end. Destination and source selectors SHALL each identify an exact unique Markdown heading; headings inside code fences SHALL not count. Before and after contributions at one destination and position SHALL follow manifest declaration order, with identical resolved destination/position/file/source-section contributions appearing once at their first occurrence. Replace and combine declarations SHALL use the declaration-order accumulator defined below; references at different destinations SHALL retain their declared placements. Output SHALL contain actual shared and inserted text with concise provenance, without separate agent reads. Inactive content SHALL not appear as instructions. Declared variable substitution in resource paths or content SHALL occur once without executing code or recursively interpreting inserted content as further selections.

#### Scenario: Python additions preserve the shared TDD flow
- **WHEN** language is python and dynamic entries use destination section, pos = "after", and source_section to select the Python scope, red, and green additions
- **THEN** each corresponding Python section appears after its target body while shared refactor and handoff content remain in their original order without TOML entries for them

#### Scenario: Shared section is referenced twice
- **WHEN** two active before or after entries reference the same source section at the same destination and position
- **THEN** it appears once there with its source label

#### Scenario: Several additions share a destination
- **WHEN** two different pos = "after" additions target the same entrypoint section
- **THEN** their content appears after that section in manifest order before the next peer or ancestor heading

#### Scenario: Section selection
- **WHEN** a dynamic entry uses source_section to identify one section of a multi-section source document
- **THEN** the output includes that section and its nested content without unrelated sibling sections

### Requirement: Resolution errors cannot yield misleading partial success

Missing selected files, source sections, or destination anchors, ambiguous heading references, malformed declarations, or content paths escaping the skill root after substitution and canonicalization SHALL produce errors. Only selected content dependencies SHALL require materialization. A failed lookup SHALL not emit a resolved result, append an unplaceable addition, or silently substitute the entire skill. Source and selection diagnostics SHALL identify the failing resource and selector.

#### Scenario: Destination anchor cannot be uniquely located
- **WHEN** an active dynamic entry names an absent or duplicated destination heading
- **THEN** lookup reports the anchor error rather than appending the addition or returning a partial procedure

#### Scenario: Missing selected section
- **WHEN** an active reference names a section that does not exist
- **THEN** the result reports the failed selection rather than returning the whole file

#### Scenario: Path escapes skill boundary
- **WHEN** an active content reference resolves outside the installed skill root
- **THEN** lookup rejects it without exposing unrelated files

### Requirement: Skill lookup is read-only and project-aware

Lookup SHALL inspect the explicitly targeted installed skill without installing, updating, or executing skills, writing variable files, or editing OpenSpec configuration. Available project values SHALL come from the invoking project's nearest applicable consumer inside its Git boundary, not from the user-level skill directory or authoring repository. A malformed nearest configuration SHALL be diagnosed rather than ignored in favor of another project. An invocation without project configuration SHALL use skill defaults where sufficient and report any required missing project inputs without inventing a project boundary.

#### Scenario: Same user-level skill in two repositories
- **WHEN** two projects invoke the same installed skill with different local variables
- **THEN** each receives its own selected content without changing the shared installation

#### Scenario: Missing project inputs
- **WHEN** a supported skill is invoked outside a configured project and requires project-specific values
- **THEN** lookup reports those missing inputs without reading a sibling repository or writing a guessed configuration

### Requirement: Selected skill content consumes its own tooling inputs

The TDD skill SHALL explicitly declare build_tool, test_runner, and test_command as inputs needed only when language is python. Its selected Python content SHALL identify the effective build/environment tool and test runner and instruct use of the effective test command with a focused test selector. These inputs SHALL follow the existing runtime precedence and configured-value prompt bypass. The skill SHALL NOT depend on the agent having read compiled OpenSpec context, copy unrelated trait guidance, or treat configured tooling as proof of installation. Missing required active inputs SHALL remain pending; unrelated language branches SHALL NOT request Python tooling.

#### Scenario: Python profile supplies tooling without OpenSpec context
- **WHEN** the Python CLI profile supplies uv, pytest, and uv run pytest and the agent invokes TDD without reading config.yaml
- **THEN** the returned Python content includes those effective tooling values without prompting for them

#### Scenario: Runtime test command override
- **WHEN** the consumer's current.toml supplies a valid test_command override for a Python TDD invocation
- **THEN** returned skill content uses that command while compile-time context configuration remains unaffected

#### Scenario: Another language is selected
- **WHEN** an installed supported non-Python branch is selected
- **THEN** the Python tooling inputs do not activate or introduce questions

### Requirement: Replace substitutes the entire destination section

For pos = "replace", resolution SHALL replace the target section identified by section, including its heading, body, and descendant subsections. The replaced range SHALL end before the next heading of equal or higher rank, or at document end. Replacement content SHALL be the selected source_section including its heading and descendants, or the complete source file if source_section is omitted. The old destination heading SHALL NOT be retained, and surrounding sections SHALL remain intact. Boundaries SHALL be determined from the original entrypoint using the same exact-heading and code-fence rules as other placements.

#### Scenario: Replace a section with nested content
- **WHEN** a dynamic entry replaces a target section containing subsections with a selected source section
- **THEN** the target heading, body, and subsections are replaced by the selected source heading and content
- **AND** the following peer or ancestor section remains intact

#### Scenario: Replace the final section using a whole file
- **WHEN** a replacement targets the final section and omits source_section
- **THEN** the target section through document end is replaced by the complete source file while preceding content remains intact

#### Scenario: Unsupported numbered placement
- **WHEN** a dynamic entry declares pos = "insert,3"
- **THEN** manifest validation reports an unsupported placement rather than guessing insertion coordinates

### Requirement: Same-target replacement supports last-wins and combine

When multiple active pos = "replace" entries target the same destination section, the last declaration in manifest order SHALL supply the replacement. Earlier replacement content SHALL NOT appear in the result, and an inactive later declaration SHALL NOT override an active one. Winner selection SHALL occur before duplicate elimination.

Resolution SHALL process active replace and combine declarations for one destination together in manifest order, beginning with an empty replacement accumulator. Replace SHALL reset the accumulator to its selected source; combine SHALL append its selected source while preserving selected headings and content. A first combine SHALL start with its source rather than the original target content. Resolution SHALL replace the whole target section once with the final accumulator and SHALL NOT perform semantic text merging. Inactive declarations SHALL neither reset nor append. Combine SHALL deduplicate source identities against contributions currently retained in the accumulator; replace SHALL reset this history as well as the content. An active replacement group on an ancestor section SHALL suppress all descendant-targeted placements, as specified below.

#### Scenario: Last active replacement wins
- **WHEN** two active replace entries target the same section
- **THEN** only the later entry supplies that section's replacement

#### Scenario: Repeated replacement returns to earlier content
- **WHEN** active same-target replace entries select A, then B, then A
- **THEN** the final replacement is A rather than B

#### Scenario: Inactive later replacement
- **WHEN** a later same-target replace entry is excluded by its condition
- **THEN** it does not override the last active replacement

#### Scenario: Combine replacement contributions
- **WHEN** two different active combine entries target the same section
- **THEN** that section is replaced once by the first contribution followed by the second, without retaining the original target content

#### Scenario: Mixed replacement and combination
- **WHEN** active entries for one target declare replace A, combine B, replace C, and combine D in that order
- **THEN** the target is replaced once by C followed by D, without A, B, or the original target content

#### Scenario: Combination starts the replacement
- **WHEN** the first active replacement-mode entry for a target is combine A
- **THEN** its accumulator starts with A and excludes the original target content

#### Scenario: Replacement clears earlier duplicate history
- **WHEN** active entries declare combine A, replace B, and combine A for one target
- **THEN** the target is replaced by B followed by A because the earlier A was discarded by replace

#### Scenario: Duplicate retained contribution
- **WHEN** active entries declare replace A, combine A, and combine B for one target using the same source identity for both A entries
- **THEN** the target is replaced by A followed by B with A appearing only once

### Requirement: Ancestor replacement takes precedence over descendant placements

Resolution SHALL derive destination boundaries and section ancestry from the original entrypoint. An active replace/combine group targeting an ancestor section SHALL suppress all entries targeting descendant sections, regardless of declaration order or placement type. This suppression SHALL apply to before, after, replace, and combine entries, including descendant after-placements sharing the ancestor's end boundary. Resolution SHALL NOT search replacement content for suppressed descendant anchors or replay descendant edits against inserted text. An inactive ancestor replacement SHALL NOT suppress child placements. Before/after entries targeting the replaced ancestor itself SHALL remain eligible and surround its final replacement.

#### Scenario: Parent replacement suppresses a later child edit
- **WHEN** an active replacement targets Red and a later entry targets its CLI tests subsection
- **THEN** the Red replacement is emitted without the child contribution
- **AND** reversing the declaration order does not change the ancestor precedence

#### Scenario: Parent combination suppresses child placements
- **WHEN** an active combine group replaces Red and before/after entries target a descendant subsection
- **THEN** the combined Red replacement is emitted without those descendant placements

#### Scenario: Inactive parent replacement
- **WHEN** every replace/combine entry for Red is inactive and an entry for its CLI tests subsection is active
- **THEN** the child placement remains eligible

#### Scenario: Replacement contains a matching child heading
- **WHEN** the selected parent replacement happens to contain a heading matching an original child destination
- **THEN** the suppressed child entry is not reapplied to that replacement content

#### Scenario: Placements surround their own target replacement
- **WHEN** before, replace, and after entries target the same Red section
- **THEN** the before content precedes the final Red replacement and the after content follows it

## MODIFIED Requirements

### Requirement: Skill support is described by pspec.toml

A supported skill SHALL carry pspec.toml beside its entrypoint, while SKILL.md owns the shared procedure and static order. Manifest version 2 SHALL declare inputs, defaults and `[[dynamic]]` additions: `section` names an exact entrypoint heading, `pos` is `after` or `replace`, `path` names a skill-relative resource with optional substitution, and optional `source_section` names an exact source heading, defaulting to the whole file. Inputs SHALL declare at most one prompt parser each.

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

### Requirement: Resolve only the invoked skill's necessary inputs

Lookup SHALL combine the skill's defaults with mounted profile defaults and explicit project or temporal values, using the consumer-configuration layers and precedence with the skill's value defaults applied last. Inputs SHALL be evaluated only when needed to select or render a reachable part of this skill; excluded branches and unrelated skills SHALL NOT request inputs. Missing values a decision needs SHALL remain pending, while invalid values or dependency cycles SHALL produce diagnostics.

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

#### Scenario: Input dependency cycle
- **WHEN** inputs depend on each other in a cycle
- **THEN** resolution reports a diagnostic instead of pending or guessing a value

### Requirement: Return selected content directly and deterministically

For `pos = "after"`, resolution SHALL keep the entrypoint's order and insert each selected addition after its destination section and descendants, before the next equal-or-higher heading or document end. Identical contributions SHALL appear once, at first occurrence; different additions at one destination SHALL follow manifest order. For `pos = "replace"`, the last active declaration for a destination SHALL replace that whole section. Output SHALL contain actual text with concise provenance.

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

#### Scenario: Headings must be exact and unique
- **WHEN** a destination or source selector matches no heading, several headings, or only a heading inside a code fence
- **THEN** resolution reports the selector instead of choosing a placement

#### Scenario: Substitution runs once without execution
- **WHEN** a resource path or inserted content contains declared variable placeholders
- **THEN** they are substituted once, without executing code or interpreting the inserted content again

### Requirement: Skill lookup is read-only and project-aware

Native --path resolution SHALL read the caller-supplied skill directory, SKILL.md or pspec.toml without discovering installations, enumerating same-named copies, checking membership, installing, updating or executing skills, writing variable files, or editing OpenSpec configuration. That location SHALL stay authoritative over other revisions or classifications; invalid locations SHALL be diagnosed without same-name fallback, and manifest references SHALL keep their containment validation.

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

### Requirement: Selected skill content consumes its own tooling inputs

The TDD skill SHALL declare build_tool, test_runner and test_command as inputs needed only when language is python, and its Python content SHALL name the effective build tool and test runner and use the effective test command with a focused selector. These inputs SHALL follow the runtime precedence and configured-value prompt bypass. The skill SHALL NOT rely on compiled OpenSpec context, copy unrelated trait guidance, or treat configured tooling as proof of installation.

#### Scenario: Python profile supplies tooling without OpenSpec context
- **WHEN** the Python CLI profile supplies uv, pytest, and uv run pytest and the agent invokes TDD without reading config.yaml
- **THEN** the returned Python content includes those effective tooling values without prompting for them

#### Scenario: Runtime test command override
- **WHEN** the consumer's current.toml supplies a valid test_command override for a Python TDD invocation
- **THEN** returned skill content uses that command while compile-time context configuration remains unaffected

#### Scenario: Another language is selected
- **WHEN** an installed supported non-Python branch is selected
- **THEN** the Python tooling inputs do not activate or introduce questions

#### Scenario: Missing Python tooling stays pending
- **WHEN** language is python and a required tooling input has no effective value
- **THEN** resolution stays pending for that input instead of guessing a tool

### Requirement: Replacement substitutes the entire destination section

For pos = "replace", resolution SHALL replace the section named by `section`, including its heading, body and descendants, up to the next heading of equal or higher rank or document end. Replacement content SHALL be the selected source_section with its heading and descendants, or the whole source file. The old heading SHALL NOT be retained and surrounding sections SHALL stay intact, with boundaries computed from the original entrypoint under the same exact-heading and code-fence rules.

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

## ADDED Requirements

### Requirement: Configured values bypass prompts without guessing

A valid effective value SHALL bypass its prompt and take precedence over prompt suggestions, while a prompt default stays a suggestion distinct from a value default. Invalid effective values SHALL produce diagnostics without substituting lower-precedence values or prompting for replacement. Conversation interpretation and answers SHALL belong to the agent, not a hidden classifier in the resolver, and resolution SHALL NOT probe repository files to infer prompt suggestions.

#### Scenario: No repository probing for suggestions
- **WHEN** an input has no effective value
- **THEN** resolution does not inspect repository files to propose a suggestion

#### Scenario: No hidden answer interpretation
- **WHEN** an input needs an answer from the user
- **THEN** resolution reports it as pending for the agent to ask, rather than interpreting conversation itself

### Requirement: Manifest interpretation is explicit and root-relative

`before`, `combine`, hint groups, `default_hint`, multiple parsers, numbered insertion and other position values SHALL produce migration diagnostics rather than being reinterpreted. Manifest references SHALL resolve relative to the supplied skill root, not the working directory. A valid manifest SHALL establish dynamic-resolution support regardless of how many inputs or dynamic entries it has or which branches are currently active.

#### Scenario: Legacy hint fields
- **WHEN** a manifest uses hint groups or `default_hint`
- **THEN** resolution reports a migration diagnostic instead of interpreting them

#### Scenario: References resolve from the skill root
- **WHEN** resolution runs from a working directory outside the skill
- **THEN** manifest paths are resolved relative to the supplied skill root

#### Scenario: Manifest without dynamic entries
- **WHEN** a valid manifest declares inputs but no dynamic additions
- **THEN** the skill is still treated as supporting dynamic resolution

### Requirement: Bundled dynamic entrypoints request their own assembly

Bundled manifest-backed entrypoints SHALL give concise instructions for requesting Powerspec content assembly after native selection, including direct invocation without generated context or a matching trait. They SHALL distinguish an unresolved entrypoint from content Powerspec already returned, and an already-resolved document SHALL NOT request itself again.

#### Scenario: Unresolved entrypoint asks for assembly
- **WHEN** an agent reads a bundled manifest-backed SKILL.md directly
- **THEN** its instructions tell the agent to request Powerspec content assembly before following dynamic steps

#### Scenario: Resolved document does not recurse
- **WHEN** an agent reads content that Powerspec has already assembled
- **THEN** that content does not instruct the agent to resolve it again

### Requirement: Project values come from the invoking consumer

Project values SHALL come from the invoking project's nearest consumer inside its Git boundary, not from the skill directory or authoring repository, with the caller keeping its task working directory. A malformed nearest configuration SHALL be diagnosed, not skipped. Without project configuration, skill defaults SHALL apply where sufficient and missing required inputs SHALL be reported without inventing a project. Agent identity SHALL supply invocation context only, never which copy is read.

#### Scenario: Malformed project configuration
- **WHEN** the nearest consumer configuration is malformed
- **THEN** resolution reports it instead of using another project's values

#### Scenario: Agent identity does not pick the copy
- **WHEN** two agents resolve the same supplied skill location
- **THEN** both read that location and differ only in invocation context

### Requirement: Skill resolution never acquires sources

Skill resolution SHALL NOT acquire or refresh remote sources to resolve supplied content. The explicit --ref route SHALL select a resource from the owning consumer's effective profile selections with the same read-only installation and input boundaries, without substituting catalog content for a native --path invocation.

#### Scenario: Catalog reference uses effective selections
- **WHEN** an agent resolves a skill with --ref
- **THEN** the resource comes from the owning consumer's effective profile selections without installing anything

#### Scenario: Native path is never replaced by catalog content
- **WHEN** a --path invocation targets a skill that also exists in the catalog
- **THEN** resolution reads the supplied path and does not substitute the catalog copy

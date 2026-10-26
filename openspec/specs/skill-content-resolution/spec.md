# Skill Content Resolution Specification

## Purpose

Resolve a supported installed skill into the content and inputs needed for its current invocation, preserving shared flow and deterministic dynamic placements.

## Requirements

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

# Spec Delta

## MODIFIED Requirements

### Requirement: Agent protocols live under resolve

`pspec resolve skill --path <selected-location> --agent <agent>` SHALL consume an explicitly supplied skill directory, SKILL.md, or pspec.toml. Relative locations SHALL be interpreted against the task's process working directory; supplying a path SHALL NOT change the directory used for consumer discovery. The agent option SHALL identify invocation context rather than drive native installation lookup. Skill resolution SHALL preserve Markdown-by-default, optional JSON, literal null for an explicitly supplied ordinary skill, and optional --change inputs. Pending responses SHALL provide a rerun command retaining the complete selected path, agent, and explicit change. JSON pending and resolved responses SHALL identify the canonical skill directory through a skill_path field while retaining their existing status, skill, agent, change, and content/questions fields; the skill name SHALL come from the selected SKILL.md's declared name.

The previous positional-name form, including the old --selected option, SHALL fail with a nonzero diagnostic explaining the new --path invocation and native-selection responsibility. It SHALL NOT perform legacy name discovery, infer a path from a bare name, or silently treat a positional name as a relative path. Exactly one of --path or --ref and an explicit --agent SHALL be required. Supplying neither selector or both selectors SHALL be an invalid invocation. --ref SHALL explicitly select the catalog route described below; it SHALL NOT revive the legacy positional-name syntax or inspect native installations. Failed invocations SHALL emit no successful payload. Both pspec and powerspec console scripts SHALL expose the same contract.

`pspec resolve hook <event> --agent <agent>` SHALL select its logical event and supported agent from command arguments and discover the nearest owning consumer from its process working directory. Optional --change SHALL remain the only selector for change-scoped hook inputs. Hook resolution SHALL NOT read, parse, poll, or wait for standard input, including when a native host supplies a payload. Protocol success SHALL write results to stdout; diagnostics SHALL use stderr and documented nonzero exit codes. Hook guidance SHALL retain the supported agent's native additional-context response envelope and an absent contribution SHALL produce no stdout.

#### Scenario: Resolve supported skill content
- **WHEN** an agent supplies the selected location of a configured skill through resolve skill --path
- **THEN** Powerspec emits that skill's resolved document in the requested representation without searching native installations

#### Scenario: Dispatch a native hook
- **WHEN** an installed agent callback invokes resolve hook with an event and agent from a consumer working directory
- **THEN** Powerspec resolves the nearest owning consumer from that directory and emits applicable hook guidance without consuming a native payload

#### Scenario: Stdin stays open
- **WHEN** hook resolution runs with an open stdin pipe whose writer sends no bytes and does not close it
- **THEN** the command completes its resolution without waiting for input or end-of-file

#### Scenario: Payload cannot redirect consumer discovery
- **WHEN** a caller supplies stdin containing another repository's cwd, malformed JSON, or arbitrary text
- **THEN** the command ignores that input and resolves only from its process working directory

#### Scenario: Direct command without a payload
- **WHEN** the user runs a supported hook resolution command with stdin closed or unavailable
- **THEN** the command uses its arguments and working directory without reporting a missing or invalid native payload

#### Scenario: Unsupported selector
- **WHEN** the caller supplies an unsupported logical event or native hook agent mapping
- **THEN** the command reports the error on stderr and exits nonzero without reading stdin or emitting successful guidance

#### Scenario: Former name-only invocation
- **WHEN** the caller runs pspec resolve skill pspec-tdd --agent codex
- **THEN** the command reports migration to --path and directs the caller to obtain the path through native skill integration without inspecting installed copies

#### Scenario: Former selected option
- **WHEN** the caller uses the previous positional-name and --selected syntax
- **THEN** the command reports that --path now carries the selected location without executing a compatibility lookup

#### Scenario: Directory and file forms
- **WHEN** the caller supplies a skill directory, its SKILL.md, or its pspec.toml using --path
- **THEN** all three forms resolve against the same skill root and preserve task-directory consumer selection

#### Scenario: Path with spaces remains usable on retry
- **WHEN** a pending invocation supplies a path containing spaces and an explicit change
- **THEN** the rerun preserves a correctly quoted path and the same agent and change, and JSON identifies the canonical skill directory

#### Scenario: Missing path is not discovery
- **WHEN** a caller omits both --path and --ref even though same-named skills are installed
- **THEN** the invocation fails without enumerating installations or selecting a default copy

#### Scenario: Console aliases agree
- **WHEN** identical explicit-path requests are made through pspec and powerspec
- **THEN** their stdout, stderr, and exit behavior agree

#### Scenario: Catalog selection is explicit
- **WHEN** the caller supplies --ref helper instead of --path
- **THEN** the command uses only selected Powerspec catalog resources and does not interpret the name as an installed skill or a filesystem path

#### Scenario: Conflicting selectors
- **WHEN** the caller supplies both --path and --ref
- **THEN** the command fails before resolving either target and emits no successful payload


### Requirement: Status and doctor inspect without mutation

`pspec status` SHALL describe the owning consumer, selected profile or global-only mode, effective profiles after exclusions, selected contexts, traits, skills, sources, and pending installation facts without acquiring or modifying resources. `pspec doctor` SHALL check the consumer boundary and required external executables and integrations without repairing them. Both commands SHALL support human-readable output and `--json`. Status SHALL distinguish skills selected for installation from resolve-skills declarations. Its existing skills JSON field SHALL retain installation-selection semantics and an additive resolve_skills field SHALL report resolve-skills selections, including declarations whose identity is also selected for installation. Human output SHALL label these two selection lists separately without implying installation success.

#### Scenario: Inspect a configured consumer
- **WHEN** a user runs status inside a valid consumer
- **THEN** Powerspec reports the effective configuration and unresolved availability facts without changing files or installations

#### Scenario: Diagnose missing prerequisites
- **WHEN** doctor finds a missing or incompatible prerequisite
- **THEN** it reports a failed named check, exits nonzero, and makes no repair attempt

#### Scenario: Inspect resolve-only availability
- **WHEN** a consumer selects a skill only through resolve-skills
- **THEN** status reports its resolution selection separately from installation selections without materializing sources or inspecting native copies


## ADDED Requirements

### Requirement: Explicit catalog skill references resolve under the owning consumer

pspec resolve skill --ref <name-or-qualified-reference> --agent <agent> SHALL resolve one resource selected by the task directory's owning consumer through effective skills or resolve-skills entries after exclusions. A bare name SHALL match the declared SKILL.md name only when it identifies exactly one distinct selected resource. An exact qualified catalog identity or concrete source-relative Git identity SHALL select only that identity when it is in the effective selections. Wildcard invocation selectors, unknown names, unselected identities, absent consumers, and ambiguous names SHALL fail with actionable diagnostics; ambiguity diagnostics SHALL identify usable exact references. Native installation state SHALL NOT establish selection or break ties.

The route SHALL support Markdown by default, --json, and explicit --change with the existing runtime value precedence. Catalog pending and resolved JSON SHALL identify status, skill, skill_ref, skill_path, agent, and change, with questions or content as appropriate. Pending retries SHALL retain the exact resolved skill_ref, task directory, agent, and explicit change. Resolved Markdown SHALL include the canonical reference and durable source root alongside the procedure; the JSON content field SHALL contain that same Markdown. An ordinary catalog skill SHALL return its procedure with resolved status rather than native-path null. Failure SHALL emit no successful payload, and both console aliases SHALL expose the same contract.

#### Scenario: Unique bare name
- **WHEN** helper is selected only through resolve-skills and has one distinct selected identity
- **THEN** --ref helper returns its content and exact identity without installing a native copy

#### Scenario: Ambiguous bare name
- **WHEN** distinct selected resources declare the same name
- **THEN** --ref with that bare name fails and identifies the exact selected references instead of preferring a source or installation scope

#### Scenario: Qualified reference disambiguates selected resources
- **WHEN** the caller supplies one exact reference identified by an ambiguity diagnostic
- **THEN** that selected resource resolves independently of other same-named resources

#### Scenario: Configured source is not selection
- **WHEN** a source contains helper but no effective profile selects that resource
- **THEN** --ref cannot resolve it, even with its exact reference

#### Scenario: Pending catalog invocation
- **WHEN** a selected dynamic skill needs an unanswered input
- **THEN** the response withholds its procedure and gives a retry preserving the concrete reference, agent, and explicitly supplied change

#### Scenario: Ordinary catalog content
- **WHEN** a selected ordinary skill has no pspec.toml
- **THEN** --ref returns resolved content while --path for that same ordinary directory retains literal null behavior

#### Scenario: No owning consumer
- **WHEN** --ref is invoked outside a configured consumer's Git boundary
- **THEN** it reports the missing consumer without searching other repositories or using arbitrary global source registrations

#### Scenario: One target produces one procedure response
- **WHEN** applicable scenario guidance or a user request leads the agent to invoke --ref A while B and C are also selected
- **THEN** stdout contains only A's resolution or pending result under the selected representation, without lifecycle progress or other candidates' procedure bodies and discovery descriptions

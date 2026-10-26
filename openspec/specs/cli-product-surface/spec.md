# Cli Product Surface Specification

## Purpose

Provide a coherent Powerspec command lifecycle for establishing, inspecting, synchronizing, installing, upgrading, configuring, and resolving a Git-bounded OpenSpec consumer.

## Requirements

### Requirement: Initialization bootstraps the consumer and selected agent

`pspec init` SHALL find the Git root, bootstrap OpenSpec without agent skills if needed, and create `openspec/.pspec/config.toml`, ignored `current.toml` and needed directories. It SHALL accept optional `--profile`, preserve compatible files and selection, allow empty selections activating global profiles, and prepare missing sources under the bounded cache policy, refreshing only with --force. Optional --agent SHALL provision that agent; invalid agents SHALL fail before file effects.

#### Scenario: Initialize an empty Git repository
- **WHEN** a user runs `pspec init --profile @builtin/python-simple-cli` inside an uninitialized consumer
- **THEN** Powerspec creates the consumer structure and records the selected profile without provisioning an agent

#### Scenario: Initialize global profiles only
- **WHEN** a user runs `pspec init` without a profile in a Git repository
- **THEN** Powerspec creates an empty profile selection that allows global profiles to apply

#### Scenario: Repeat initialization
- **WHEN** initialization without --force is repeated for a compatible existing consumer
- **THEN** Powerspec preserves persistent and temporary values and reports the established consumer while reusing matching sources and requested agent installations

#### Scenario: Initialize with an agent
- **WHEN** a user runs pspec init --agent codex for a valid bundle
- **THEN** missing selected sources, profile-scoped skills, and user-level hooks are prepared without a separate install command

#### Scenario: Interactive init confirms conflict replacement
- **WHEN** a user runs pspec init --agent claude in an interactive terminal and selected skills exist as differing unowned copies
- **THEN** init installs non-conflicting skills, lists the conflicting skills, and asks once whether to replace them
- **AND** on acceptance the conflicts are recoverably replaced and init completes in the same invocation

#### Scenario: Interactive init declined
- **WHEN** the user declines the replacement confirmation
- **THEN** the conflicting copies are unchanged, init reports incomplete setup naming `pspec init --agent claude --force`, and published source selections remain usable by upgrade and sync

#### Scenario: Non-interactive init with conflicts
- **WHEN** init --agent runs without interactive terminals and selected skills conflict
- **THEN** init does not prompt, leaves the conflicts unchanged, and reports the --force remedy

#### Scenario: Invalid agent
- **WHEN** init receives an unsupported agent
- **THEN** it reports the error before creating consumer files or acquiring sources

#### Scenario: Force initialization without an agent
- **WHEN** a user runs pspec init --force
- **THEN** all selected sources are explicitly refreshed and validated before selection publication, without installing agent assets or publishing contexts

#### Scenario: Force initialization with an agent
- **WHEN** a user runs pspec init --agent codex --force
- **THEN** sources are explicitly refreshed after any necessary provider-verified manager migration, then guarded provisioning recoverably replaces completely inspected unowned or modified selected skills without prompting and permits source-matching owned hook receipt repair while preserving unrelated assets

#### Scenario: Local scope
- **WHEN** a user runs pspec init --scope local
- **THEN** the consumer and published source selections are established and no agent skills or hooks are inspected or written

#### Scenario: Global scope without selections
- **WHEN** a user runs pspec init --scope global --agent claude for a consumer with no published selection for a required source
- **THEN** init fails without acquiring sources and directs the user to run pspec init or pspec init --scope local

#### Scenario: Discover the refresh override
- **WHEN** a user reads init help
- **THEN** --force is described as refreshing sources, authorizing verified migration of a supported unmanaged default manager when needed, recoverably replacing conflicting selected skills, and permitting guarded hook receipt repair for an explicitly selected agent

#### Scenario: Later failure keeps completed setup
- **WHEN** a step fails after the consumer was established
- **THEN** init keeps the completed setup and reports incomplete bootstrap for retry

### Requirement: First-use source preparation preserves existing stores

Source preparation SHALL delegate missing-store initialization and managed launcher publication to Saucepan's official setup contract, never publishing a raw manager at the default launcher path or moving installer leftovers. An unmanaged occupant SHALL need explicit Saucepan migration (external or init --force) or a standalone override; ordinary init and upgrade SHALL NOT supply migration consent. It SHALL NOT replace credentials, delete store data, bypass guards or substitute test keys.

#### Scenario: Fresh native store
- **WHEN** a store is absent and Saucepan permits initialization
- **THEN** Saucepan setup completes the managed installation before PowerSpec registers its resource-consumer application and continues acquisition

#### Scenario: Existing store cannot be initialized
- **WHEN** Saucepan rejects initialization because existing data or credential problems prevent it
- **THEN** PowerSpec reports failure without registering or acquiring sources or replacing store contents

#### Scenario: Failed binary-only setup
- **WHEN** the former installer left only recognized installer files under the default root
- **THEN** rerunning init preserves those files in place and reports the provider-supported manual preservation or separate-root prerequisite without moving them

#### Scenario: Canonical GitHub source identity
- **WHEN** Saucepan returns the same HTTPS GitHub repository with canonical lowercase owner/repository spelling and the normal .git suffix
- **THEN** source preparation accepts that identity while preserving host, transport, query, and reference distinctions; other hosts retain case-sensitive repository paths

#### Scenario: Credential or store failure stays an error
- **WHEN** the credential service fails or the store is damaged
- **THEN** source preparation reports an error and claims no success

#### Scenario: Uncertain provider setup
- **WHEN** provider setup fails or its outcome is uncertain
- **THEN** the user is directed to inspect and resume the original provider operation where applicable, then rerun init with the same source options

#### Scenario: Upgrade does not replace missing initialization
- **WHEN** a consumer's sources were never initialized
- **THEN** upgrade does not silently perform that missing initialization

### Requirement: No separate install command
The public CLI SHALL expose agent bootstrap through init and SHALL NOT expose an install command. Help and bundled bootstrap guidance SHALL direct users to init --agent for provisioning.

#### Scenario: Discover setup command
- **WHEN** a user reads root and init help
- **THEN** init offers --agent and root help has no install command

### Requirement: Status and doctor inspect without mutation

`pspec status` SHALL describe the owning consumer, selected profile or global-only mode, effective profiles after exclusions, selected contexts, traits, skills, sources and pending installation facts without acquiring or modifying resources. `pspec doctor` SHALL check the consumer boundary and required executables and integrations without repairing them. Both SHALL support human and `--json` output, and status SHALL report installation-selected skills separately from resolve-skills declarations.

#### Scenario: Inspect a configured consumer
- **WHEN** a user runs status inside a valid consumer
- **THEN** Powerspec reports the effective configuration and unresolved availability facts without changing files or installations

#### Scenario: Diagnose missing prerequisites
- **WHEN** doctor finds a missing or incompatible prerequisite
- **THEN** it reports a failed named check, exits nonzero, and makes no repair attempt

#### Scenario: Inspect resolve-only availability
- **WHEN** a consumer selects a skill only through resolve-skills
- **THEN** status reports its resolution selection separately from installation selections without materializing sources or inspecting native copies

#### Scenario: Status JSON keeps the skills field meaning
- **WHEN** status reports a skill that is both selected for installation and declared in resolve-skills
- **THEN** the skills field keeps installation semantics, the additive resolve_skills field also lists it, and human output labels the two lists separately without implying installation success

### Requirement: Synchronization is local-aware and atomic

`pspec sync` SHALL compose bundled, consumer-local and selected remote resources, resolve conditions against the owning consumer, validate every required resource, and only then atomically reconcile managed guidance in `openspec/config.yaml`, preserving user YAML and the original file on failure. It SHALL acquire missing selected sources while reusing existing materializations without refresh, and successful acquisitions SHALL stay available if later validation fails.

#### Scenario: Publish local and bundled contexts
- **WHEN** a consumer-local resource overrides or extends selected bundled guidance and all required resources are available
- **THEN** sync publishes the effective contributions once while preserving user-authored content

#### Scenario: Required source is unavailable
- **WHEN** a selected remote resource is not already materialized
- **THEN** sync attempts its first acquisition; a failure reports the unavailable resource and leaves `config.yaml` byte-for-byte unchanged

#### Scenario: Fresh machine
- **WHEN** selected sources have never been materialized
- **THEN** sync prepares Saucepan, acquires those sources, and publishes after complete validation

#### Scenario: Preserve current remote revision
- **WHEN** upstream has newer content than the current materialization
- **THEN** sync reuses the current revision; refreshing it requires upgrade

### Requirement: Upgrade refreshes before committing removals

`pspec upgrade --agent <agent>` SHALL refresh selected Saucepan sources, compose the refreshed bundle, reconcile skills and hooks, and remove obsolete managed installations only after every required refresh and reconciliation step succeeds. It SHALL reuse a compatible Saucepan installation without self-updating the shared manager, reporting provider update guidance before refresh when incompatible. `sync` SHALL keep preserving the currently materialized revisions.

#### Scenario: Successful upgrade
- **WHEN** all selected sources refresh and the resulting installation succeeds
- **THEN** Powerspec commits additions, updates, and obsolete managed removals for the agent

#### Scenario: Upgrade fails before completion
- **WHEN** any required refresh or reconciliation step fails
- **THEN** Powerspec reports failure without committing obsolete-source removals

#### Scenario: Skill force does not repair hooks
- **WHEN** upgrade uses --force without --repair-hooks and finds a stale hook receipt
- **THEN** it reports hook reconciliation failure and preserves obsolete skills

#### Scenario: Authorized hook repair
- **WHEN** upgrade uses --repair-hooks and a valid stale receipt identifies hooks already matching the desired source
- **THEN** ownership is repaired through ZuAT, its recovery identifier is displayed, and upgrade continues after successful reconciliation

#### Scenario: Ambiguity despite repair option
- **WHEN** upgrade uses --repair-hooks but hook identity is unresolved
- **THEN** upgrade exits nonzero without claiming success or removing obsolete skills

### Requirement: Configuration and temporary state have explicit groups

`pspec config show` SHALL display persistent configuration, `pspec config profile [PROFILE]` SHALL set or clear the selected profile preserving other configuration, and `pspec config edit` SHALL open the persistent configuration in the user's editor. `pspec state show` SHALL display temporary global and change-scoped values, and `pspec state clear [--change CHANGE]` SHALL clear only the selected temporary scope, preserving persistent configuration. Read commands SHALL support `--json`.

#### Scenario: Change the selected profile
- **WHEN** a user sets or clears a profile through `config profile`
- **THEN** Powerspec updates only the persistent profile selector and leaves variables intact

#### Scenario: Clear one change
- **WHEN** a user runs `state clear --change example`
- **THEN** Powerspec removes only `_change.example` temporary values and preserves global temporary and all persistent values

### Requirement: Agent protocols live under resolve

`pspec resolve skill --path <selected-location> --agent <agent>` SHALL consume a supplied skill directory, SKILL.md or pspec.toml, resolving relative paths from the process working directory without changing consumer discovery; --agent SHALL be invocation context only. It SHALL keep Markdown by default, optional JSON, null for ordinary skills and optional --change. Pending responses SHALL give a rerun command keeping the full path, agent and change, and JSON responses SHALL add skill_path.

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

#### Scenario: JSON responses keep their fields
- **WHEN** a skill resolves or is pending with --json
- **THEN** the response keeps its status, skill, agent, change and content or questions fields, adds skill_path, and takes the skill name from the selected SKILL.md

### Requirement: Commands present stable human and JSON results

Human-facing lifecycle commands SHALL emit concise successful outcomes to stdout and actionable diagnostics to stderr. Commands that support `--json` SHALL emit exactly one JSON value on stdout and no human decoration. Operational failures SHALL exit nonzero and SHALL NOT emit a success claim.

#### Scenario: Request structured status
- **WHEN** a caller runs `pspec status --json`
- **THEN** stdout contains one parseable result object and diagnostics, if any, remain on stderr

#### Scenario: Operation fails
- **WHEN** a command cannot complete its promised effect
- **THEN** it exits nonzero and identifies the failed operation without a contradictory completion message

### Requirement: Doctor distinguishes executable checks from source readiness

Doctor SHALL label its successful Saucepan observation as an executable compatibility check, without implying initialized materializations. For the default managed route it SHALL separately inspect setup status when supported, distinguishing ready, unmanaged, absent, pending and conflict, since version alone SHALL NOT establish managed ownership. An explicit override SHALL be labelled standalone and inspected without adoption or update. Results SHALL state this limitation without mutation.

#### Scenario: Compatible binary but no selected source
- **WHEN** doctor observes a compatible Saucepan executable
- **THEN** its detail identifies executable compatibility, reports managed installation status separately when applicable, and states that selected-source readiness was not checked

#### Scenario: Compatible raw binary at the default path
- **WHEN** a version-compatible raw manager occupies the default managed launcher path
- **THEN** doctor distinguishes executable compatibility from missing managed ownership and reports explicit migration guidance without modifying the file

#### Scenario: Explicit standalone override
- **WHEN** the user selects an external manager through POWERSPEC_SAUCEPAN
- **THEN** doctor labels that selection standalone without requiring managed ownership or changing the binary

#### Scenario: Recovery guidance separates setup from init
- **WHEN** doctor reports an incomplete provider setup
- **THEN** its instructions distinguish explicit provider setup recovery from later source initialization with init before upgrade

### Requirement: Doctor reports evidence for guidance delivery stages

`pspec doctor --agent codex|claude` SHALL add read-only diagnostics distinguishing effective zmem profile selection, current persistent rule publication, matching startup/compaction registrations, observable disabled settings, resolver generation for both events, and host receipt/adherence. Resolver generation SHALL use the installed hook command with finite timeouts and validate its envelope, keeping source warnings visible. Doctor SHALL NOT install, enable, trust, repair or acquire resources.

#### Scenario: Hook registered but disabled
- **WHEN** native settings explicitly disable a matching PowerSpec callback
- **THEN** doctor reports the observed disabled setting and exits unsuccessfully without changing it

#### Scenario: Guidance generated without host observation
- **WHEN** both resolver commands emit valid context
- **THEN** generation passes while host receipt and adherence remain unverified

#### Scenario: Stale or missing published context
- **WHEN** the zmem profile is selected but the current standing rule is absent from config.yaml
- **THEN** doctor reports the publication gap rather than claiming complete delivery

#### Scenario: Missing sources
- **WHEN** resolver output contains metadata warnings but still carries the required rule
- **THEN** doctor preserves those warnings and does not repair sources

#### Scenario: Excluded policy
- **WHEN** zmem is excluded
- **THEN** doctor reports intentional nonselection without treating its absent guidance as a failure

### Requirement: Lifecycle commands expose active work while waiting

Init, including source-only init, and upgrade SHALL emit progress on stderr before potentially blocking work and report item outcomes as they occur, naming consumer setup, manager preparation, source identity and stage, skill identity and count, hooks, and selection publication or removal/recovery when reached. Source progress SHALL distinguish reuse of a validated selection, cache-eligible preparation and explicit refresh, never claiming a cache hit or download without provider evidence.

#### Scenario: Native source operation takes time
- **WHEN** init waits on Saucepan to prepare a selected source
- **THEN** stderr identifies that source before the wait and continues reporting the active stage and elapsed waiting without requiring native output

#### Scenario: Earlier item fails
- **WHEN** one skill has a returned ownership conflict and later skills remain to be checked
- **THEN** the conflict is reported before the later checks finish, without claiming ownership or successful completion

#### Scenario: Source-only initialization
- **WHEN** init runs without an agent and prepares sources
- **THEN** source progress is visible without installing agent assets

#### Scenario: Redirected command output
- **WHEN** stdout and stderr are redirected to separate streams
- **THEN** readable progress remains on stderr and stdout retains only its existing results

#### Scenario: Existing selected source is reused
- **WHEN** init validates an existing consumer binding without acquisition
- **THEN** stderr reports retained selection reuse without suggesting materialization or a network refresh occurred

#### Scenario: A new consumer prepares a source
- **WHEN** init requests preparation using the 24-hour cache policy and the provider exposes no hit or transfer telemetry
- **THEN** progress describes preparation with cache reuse allowed, without claiming either a hit or a download

#### Scenario: Force requests refresh
- **WHEN** init --force starts a source operation
- **THEN** progress identifies the explicit refresh request and preserves normal waiting, failure, and stdout behavior

### Requirement: Progress observation preserves failure and recovery boundaries

Progress SHALL stop when an operation completes, fails or is interrupted, with no later waiting event for that stage. Failures and timeouts SHALL identify the active operation and elapsed time while preserving original diagnostics, nonzero exits and retry or pending guidance. A heartbeat SHALL NOT extend deadlines, retry mutations, change source selection, bypass native ownership or assert rollback. Library calls without an observer SHALL stay silent.

#### Scenario: Source request times out
- **WHEN** source preparation reports a timeout after starting a mutation
- **THEN** the command identifies the failed source stage and elapsed wait, reports the existing uncertain-state guidance and leaves pending receipts governed by the existing retry contract

#### Scenario: Completed or interrupted operation
- **WHEN** an operation exits normally or through interruption
- **THEN** its progress worker shuts down and no later waiting line is emitted for it

#### Scenario: Protocol invocation
- **WHEN** a caller resolves hook or skill guidance or requests doctor JSON
- **THEN** lifecycle progress does not pollute the response

### Requirement: Forced initialization authorizes bounded recovery

Init --force SHALL authorize provider-verified unmanaged-manager migration when needed and, with an explicit agent, guarded hook receipt repair and recoverable replacement of completely inspected unowned or modified skills. It SHALL NOT authorize replacing incompletely inspected or unsupported skills or hook content, manager self-update, or bypassing provider preflight. Progress SHALL name recovery operations and identifiers, and completed recovery SHALL stay reported if later steps fail.

#### Scenario: Forced init repairs a matching hook receipt
- **WHEN** init --agent codex --force encounters a valid owned stale receipt with a uniquely identified source-matching hook group
- **THEN** ZuAT performs guarded receipt-only repair, preserving native bytes and modification time, and init reports its operation identifier

#### Scenario: Forced init replaces a conflicting skill
- **WHEN** init --agent codex --force finds a completely inspected selected skill with differing unowned or modified content
- **THEN** ZuAT archives and replaces it and init reports the replacement and its operation identifier

#### Scenario: Hook content changes concurrently
- **WHEN** hooks cease to match the desired source between inspection and authorized repair
- **THEN** the provider rechecks source equality inside the operation and rejects repair without replacing those hooks

#### Scenario: Forced init cannot establish hook identity
- **WHEN** hook inspection is incomplete, identity is ambiguous, the receipt is invalid, or content is locally edited
- **THEN** forced initialization fails with diagnostics without positional overwrite or an installation fallback

#### Scenario: No agent is selected
- **WHEN** init --force runs without --agent
- **THEN** no native hooks or skills are inspected, repaired or replaced and no agent is inferred

#### Scenario: Later source preparation fails after migration
- **WHEN** verified manager migration succeeds but a subsequent source operation fails
- **THEN** init reports overall failure and the completed migration separately, retaining provider backups and recovery evidence without claiming rollback

### Requirement: Explicit catalog skill references resolve under the owning consumer

`pspec resolve skill --ref <selector> --agent <agent>` SHALL retrieve one skill from the owning consumer's effective skills or resolve-skills after exclusions. Bare names SHALL uniquely match declared names; exact references SHALL identify selected resources. Invalid, wildcard, absent, unselected or ambiguous selectors SHALL fail without a successful payload or native lookup. Catalog results SHALL preserve identity, runtime precedence and the output contracts in the scenarios below.

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

#### Scenario: Represent one catalog result
- **WHEN** either console alias resolves a catalog target
- **THEN** JSON identifies status, skill, skill_ref, durable skill_path, agent and change, plus content or questions as appropriate
- **AND** resolved content equals default Markdown, including the canonical reference and source directory; runtime input precedence remains unchanged
- **AND** a pending retry retains the concrete reference, task directory, agent and explicit change

#### Scenario: Invalid catalog selector
- **WHEN** the caller supplies a wildcard, unknown name, unselected identity or ambiguous bare name
- **THEN** resolution fails with an actionable diagnostic and no successful payload
- **AND** ambiguity lists usable exact references without using native installations to establish membership or break ties

### Requirement: Init resolves skill conflicts in one run

One `pspec init --agent <agent>` SHALL suffice when selected skills exist as fully inspected unowned or modified copies. With interactive stdin and stderr and no --force, init SHALL list those skills once, note that originals are recoverably backed up, and ask once, defaulting to no; accepting SHALL replace them under the bounded replacement contract. Declining, or running without interactive terminals (never prompted), SHALL leave them unchanged and name `pspec init --agent <agent> --force`.

#### Scenario: Confirmation defaults to no
- **WHEN** the user answers the replacement confirmation without typing yes
- **THEN** no skill is replaced

#### Scenario: Conflicts are listed once
- **WHEN** several selected skills conflict
- **THEN** init lists them together and asks a single confirmation

### Requirement: Init scope selects local or global setup

Optional `--scope` SHALL accept `local`, `global` or `all`, defaulting to `all`, which performs both. `local` SHALL establish the consumer and prepare and publish sources without inspecting or writing agent assets, and SHALL reject --agent. `global` SHALL require --agent and provision skills and hooks from published selections without acquiring, refreshing or publishing sources or rewriting consumer files, failing with local-init guidance when a selection is missing.

#### Scenario: Local scope rejects an agent
- **WHEN** a user runs pspec init --scope local --agent codex
- **THEN** init fails before any effects and explains that local scope provisions no agent assets

#### Scenario: Global scope requires an agent
- **WHEN** a user runs pspec init --scope global without --agent
- **THEN** init fails before any effects

### Requirement: Upgrade hook repair needs its own flag

Upgrade SHALL accept `--repair-hooks` to repair a valid stale hook receipt whose uniquely identified native hooks already match the desired source, while `--force` stays limited to skill replacement. Repair SHALL NOT replace arbitrary hooks or act on incomplete inspection; failures SHALL keep provider diagnostics and recovery identifiers, and success SHALL show its operation. Ordinary init SHALL NOT authorize receipt repair; init --force with an explicit agent SHALL authorize it.

#### Scenario: Ordinary init does not repair receipts
- **WHEN** ordinary init finds a stale hook ownership receipt
- **THEN** it reports the problem without repairing the receipt

#### Scenario: Repair displays its operation
- **WHEN** an authorized hook repair succeeds
- **THEN** upgrade displays the recovery operation identifier

### Requirement: Skill resolution requires one explicit selector

Exactly one of --path or --ref and an explicit --agent SHALL be required; neither or both selectors SHALL be invalid. The former positional-name form and --selected option SHALL fail with a diagnostic explaining --path and native selection, without name discovery or treating a name as a path. --ref SHALL select the catalog route without reviving positional names or inspecting native installations. Failures SHALL emit no successful payload, and pspec and powerspec SHALL share this contract.

#### Scenario: Agent is required
- **WHEN** pspec resolve skill is invoked without --agent
- **THEN** it fails as an invalid invocation

#### Scenario: Failure emits no payload
- **WHEN** a skill resolution invocation fails
- **THEN** stdout contains no successful result

### Requirement: Hook resolution reads only its arguments

`pspec resolve hook <event> --agent <agent>` SHALL take its logical event and agent from arguments, discover the nearest owning consumer from its working directory, and use optional --change as the only change selector. It SHALL NOT read, parse, poll or wait for stdin, even when a host supplies a payload. Results SHALL go to stdout in the agent's native additional-context envelope, with diagnostics on stderr and documented nonzero exits; no contribution SHALL produce no stdout.

#### Scenario: No contribution writes nothing
- **WHEN** no trait contributes guidance for the event
- **THEN** hook resolution writes nothing to stdout

#### Scenario: Change selector for hook inputs
- **WHEN** hook resolution needs change-scoped inputs
- **THEN** only an explicit --change argument selects that change

### Requirement: Doctor reports unverifiable delivery honestly

Host receipt, effective enablement or trust beyond inspected settings, and adherence SHALL be reported unverified unless directly established; generation alone SHALL NOT establish them. Unknown verification SHALL be a warning, observed failures SHALL exit nonzero, and JSON SHALL stay one structured result. Unsupported agents SHALL fail before probes, and omitting --agent SHALL keep basic checks and note that delivery checks were not requested.

#### Scenario: Unsupported agent fails before probes
- **WHEN** doctor receives an unsupported --agent
- **THEN** it fails before running any delivery probe

#### Scenario: Delivery checks not requested
- **WHEN** doctor runs without --agent
- **THEN** it runs basic checks and reports that delivery checks were not requested

### Requirement: Waiting heartbeats claim nothing

The innermost active stage SHALL report elapsed waiting every five seconds while blocked, without claiming upstream activity, measured transfers or completion percentages. Successful results SHALL keep their stdout and exit contracts, and progress SHALL NOT activate for unrelated JSON or resolution protocols.

#### Scenario: Heartbeat claims no transfer
- **WHEN** a waiting line is printed during a blocked stage
- **THEN** it reports elapsed time only, without transfer amounts or percentages

#### Scenario: Results keep their stdout contract
- **WHEN** a lifecycle command succeeds with progress enabled
- **THEN** its stdout results and exit status are unchanged by progress output

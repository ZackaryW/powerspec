# Design

## Context

See `proposal.md` for motivation. Powerspec currently provisions two user-level context-delivery commands through ZuAT. Codex maps sessionStart to `startup|resume|clear`; Codex Desktop can present ordinary turns as resume, putting catalog composition and every eligible runtime probe on the prompt path. Generated handlers omit the native timeout, so Codex applies its 600-second default. Runtime conditions are currently collected atomically, causing one optional integration failure to discard unrelated guidance.

The dispatcher must remain consumer-aware: the same user installation serves different Git repositories and worktrees by resolving the nearest `openspec/.pspec/config.toml` from the native payload. Static installation-time rendering would lose that property.

## Goals / Non-Goals

**Goals:**

- Start Powerspec only at native events that establish or reconstruct model context.
- Bound host waiting independently of internal subprocess behavior.
- Keep condition observations fresh at those boundaries without adding a persistent cache.
- Preserve independent guidance when an optional external command probe fails.
- Upgrade safely owned older callback shapes while preserving third-party hooks.

**Non-Goals:**

- Enforce policy before or after every tool call or prompt.
- Manage GitKraken, ZPP, or other providers' hook entries.
- Cache service readiness in project or user state.
- Move the Zmem service-doctor check into `pspec doctor` or compile it into `config.yaml`.
- Add a general scheduler, daemon, or background service.

## Decisions

### Use a strict native event allowlist

Codex sessionStart maps to `startup|clear`; Claude maps to `startup|clear|fork`; afterCompaction continues to use each host's verified compact context-delivery event. Resume and all prompt/tool/permission/stop events are absent from generated documents.

This uses the cheapest reliable gate: when a native matcher does not select Powerspec, no Python process, catalog load, profile composition, or doctor command starts. A dispatcher-side check would still pay most startup cost. A per-session cache was rejected because it adds state, invalidation, and cleanup while still starting a process on every resume.

### Bound native and nested execution separately

Generated advisory handlers carry a five-second native timeout and a status message. Runtime Invocation accepts a probe timeout below its existing five-second default; hook dispatch supplies a smaller budget so it can handle failure and serialize output before the native deadline.

The native timeout protects against stalls in Python startup, filesystem access, catalog loading, external commands, and unforeseen defects. The nested timeout provides a controlled diagnostic for command probes rather than relying on the host to terminate the whole dispatcher. One timeout alone cannot provide both guarantees.

### Isolate operational probe failures at the hook boundary

Trait selection occurs before condition evaluation. Hook dispatch evaluates matched traits independently and distinguishes operational command-probe failures from authored configuration errors. A command launch, exit, timeout, or JSON-data failure records a resource-specific diagnostic and omits that optional trait; unrelated successful bodies remain deliverable. Syntax, missing required bindings, and non-Boolean authored results remain configuration errors.

This exception is specific to advisory hook delivery. Context synchronization retains atomic publication. Treating probe failure as ordinary false was rejected because it hides service problems; preserving the current all-or-nothing hook result was rejected because an optional Zmem outage could remove bootstrap or accessibility guidance.

### Reconcile only safely owned Powerspec registrations

The desired ZuAT hook asset contains only current `pspec resolve hook` entries. When ownership metadata establishes that the observed native bytes still equal the managed baseline, provisioning updates the asset and lets ZuAT remove obsolete owned aliases or broader matchers. Unmanaged or user-modified entries remain conflicts rather than overwrite candidates. Entries belonging to other providers are preserved by semantic merge.

Direct pattern-based deletion of arbitrary native hooks was rejected because command text is not sufficient ownership evidence.

### Keep the existing resource model

Traits retain their `hooks`, `body`, and optional Python `when`. The Zmem lifecycle trait continues to call `zmem service doctor`; ADHD-friendly continues to read its configured variable. Their cadence changes through native mapping, so no authored resource migration or persistent readiness file is required.

No generic utility is introduced. Timeout selection and trait error policy are application-level condition and delivery responsibilities rather than portable domain-neutral helpers.

## Risks / Trade-offs

- **A resumed conversation may not receive a repeated bootstrap reminder** -> Startup, clear, fork, and compact remain covered; installed skills remain directly callable, and avoiding per-turn blocking takes priority over redundant reinjection.
- **A five-second host deadline may discard guidance on an unusually slow machine** -> The nested probe budget leaves headroom, normal measured resolution is below one second, and advisory guidance must fail open rather than block the session.
- **Partial hook guidance can accompany an operational diagnostic** -> Isolation is limited to external probe failures and retains resource identity; authoring errors remain hard failures.
- **Corrupt ZuAT ownership history can prevent automatic migration** -> Provisioning reports the registry problem without overwriting native configuration; manual repair remains separate from callback generation.

## Migration Plan

1. Release the narrowed callback definitions and bounded handler metadata.
2. On `pspec init --agent <agent>` or `pspec upgrade --agent <agent>`, reconcile safely owned earlier Powerspec hook assets through ZuAT.
3. Verify the resulting native document contains only startup/clear/fork and compact mappings with explicit timeouts, alongside preserved unrelated providers.
4. If migration fails ownership checks, leave the existing file unchanged and report the exact conflict; users can repair the registry or remove stale owned entries before retrying.

Rollback restores the previous callback mapping through the same ownership-aware update. It must not reconstruct or remove unrelated hook entries.

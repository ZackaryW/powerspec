# Design

## Context

See proposal.md. The prior changes provide profile/consumer resolution, working skill lookup, packaged resources, and scoped ZuAT provisioning. Hook remains a CLI placeholder. The global builtin source now names both the bootstrap skill and its unconditional skill-bootstrap runtime trait. Their TOML shape and references have been checked; native delivery remains unimplemented.

Prerequisites: establish-profile-consumer-resolution, implement-skill-content-resolution, and bundle-resources-and-initialize. Remote sources are not a dependency.

## Goals / Non-Goals

**Goals:** Deliver a bootstrap reminder using trait selection at native session start and after compaction, from generic user-level registrations.

**Non-Goals:** Put hooks on profiles, compile hook bodies into config.yaml, execute testing workflows, evaluate all skill inputs, or guarantee agent adherence after delivery.

## Decisions

### Verified native delivery mappings

Powerspec supports Codex CLI 0.159.1 and Claude Code 2.1.265 through each
host's `SessionStart` callback. `sessionStart` maps to the native sources
`startup|resume|clear` on Codex and `startup|resume|clear|fork` on Claude.
`afterCompaction` maps to `SessionStart` with source `compact` on both hosts.
Both hosts accept `hookSpecificOutput.hookEventName = "SessionStart"` with
`additionalContext` for model-visible guidance. Their native `PostCompact`
callbacks can execute a command but cannot deliver that context, so Powerspec
does not claim them as supported delivery mappings. Kimi and Pi remain
unsupported until equivalent context-capable contracts are verified.

Runtime traits are resources under traits/ with hooks/body and optional Python when, without a mode discriminator. Compile-time contexts live under contexts/ and are selected through profiles contexts lists. Their publication belongs to implement-context-sync, which is not a dependency of hook delivery. Skills retain their own dynamic variable resolution. zmem health gating is runtime-trait work using the foundation's run_json capability; bundle/source-adapter migration remains follow-up work.

### Traits own guidance and selectors

Declare hooks = ["sessionStart", "afterCompaction"], and body directing the agent to <skill:pspec-skill-bootstrap>. Reference the trait from builtin alongside the skill. Reuse the foundation's context/trait shape validation; context attachments never enter dispatch.

The bootstrap reference identifies the installed normal skill name. Traits may declare a Python when expression through the foundation's capabilities. It controls inclusion, without making body strings executable or broadening their interpolation contract.

### Shared installation and per-consumer dispatch are separate

ZuAT provisions one reusable command surface for supported callbacks at user scope for the explicit agent. Do not encode one consumer/profile/body in shared settings. Profile skill scope does not move these hooks.

Callbacks invoke pspec hook <event> with adapter context carrying actual agent, native event identity, and event cwd. Finalize the exact transport from verified native callback payloads; validate it rather than inferring cwd from the executable location. Reuse Git-bounded nearest-consumer discovery, including worktrees. No consumer/no match yields no guidance. Malformed nearest config reports a diagnostic rather than fallback. Dispatcher plumbing does not install, write state, prompt, resolve unrelated skill inputs, or run skills. Trusted condition methods/probes can have effects that the executor does not isolate or roll back.

### Python conditions are evaluated at invocation

Resolve the consumer and event selectors/exclusions before evaluating each eligible trait's top-level when. Reuse the foundation's case18 adapter with which, git_root Path, effective runtime vars, and run_json bound to the event cwd/environment. Runtime change layers participate only with an explicit caller selector, never inferred active change. Variable keys cannot replace capabilities.

Omission is unconditional; actual false omits only the trait's body. Preserve other matching contributions and generic native registrations. Use fresh namespaces/observations every callback, no persisted or cross-call cached answers, and ordinary Python short-circuit order. Skill manifests retain their distinct contract without unrelated input questions.

The foundation owns strict Boolean/error outcomes and run_json's no-shell argv execution, object JSON, exit-zero requirement, and five-second subprocess timeout. An ok=false object is data; failed execution or malformed JSON is an error. Return no successful partial payload after an eligible expression fails. No consumer or no eligible contribution runs no condition. Marker presence is not index health.

Conditions are trusted rules. Dispatch plumbing does not install/write state/run skills, but exposed methods/commands can have effects and case18 has no whole-expression limits or rollback. Use injected capabilities and disposable consumers/settings. Leave bootstrap unconditional. Pass the completed effective bundle to armed; event eligibility and when outcomes never mutate its selection snapshot. Migrate no CodeGraph/zmem resources automatically; the combined repository-investigation bundle follows this delivery milestone.

### Exclusions affect one trait on one named native callback

Powerspec owns logical names, native qualified selectors, ~ exclusions, event mappings, and native response serialization. ZuAT owns native asset management. Expand positives per trait, then remove that trait's named excluded native callbacks. Other traits and other callbacks for the same logical event remain eligible; generic registration remains installed even if nothing contributes.

The example ["afterCompaction", "~claude:postcompaction"] expresses the intended selection syntax, not a verified native event spelling. Verify accepted callback identities before publishing mappings. Do not invent callback names from the logical vocabulary.

### Delivery requires more than successful command execution

Verify both sessionStart and afterCompaction mappings against supported hosts. A command-only callback that cannot inject context does not fulfill delivery. Serialize output in the target host's actual accepted response form; unsupported mappings are reported.

Reuse matching registrations without duplicate callbacks, preserve unrelated settings, and report unmanaged/modified conflicts and partial outcomes. Initialization integrates registration only after this capability exists. Keep evidence for installation, invocation, context delivery, agent adherence, and skill execution separate.

## Risks / Trade-offs

- A host supports execution but not guidance at a callback: mark the mapping unsupported instead of claiming delivery.
- Shared registration could leak one repo's configuration: resolve at event time from supplied cwd.
- A trait exclusion could accidentally disable another trait: verify per-trait selection independent of registration lifecycle.
- Conditions invoke host capabilities: document the trusted-rule boundary and distinguish subprocess timeout from evaluator isolation.

## Migration Plan

Verify native payload/response contracts, add selector mapping and dispatch, author the builtin trait, then integrate generic provisioning. Use isolated native settings; do not mutate the real home during verification.

Run a walkthrough with ordinary null fallback, pending TDD, an answered rerun, broken manifest, and environment-only work. Show delivered reminders without claiming a testing workflow executed. Returning to the previous package must not delete unrelated hook assets. Broader hook events, sync, and archive cleanup remain deferred.

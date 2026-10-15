# Design

## Context

See proposal.md. `pyproject.toml` pins the old SDK at 4e22ad0. `sources.py` imports Saucepan, string-matches failures, models legacy view/history/artifacts, and shares a class-level APP name. `saucepan_tool.py` and `doctoring.py` import the removed shared_executable_path helper and accept 0.5/0.6. `workspace.open_workspace` already separates lookup and ensure; `statusing.py` and hook resolution depend on read-only inspection and deadlines. `upgrading.py` owns validation/ZuAT provisioning and the all-success removal boundary.

Current Saucepan SDK evidence: `sdk/python`, operations inventory and resource group/pin fixtures at commit `041e4f90634e6007b58054a59604396f8fbebd21`. SDK version 0.1.0 targets the new manager contract shipped as 0.9.0; there is no guarantee an old SDK with the same package name works.

## Goals / Non-Goals

### Follow-on 0.10 profile adoption

The authorized follow-on updates the dependency to SDK 0.2.0 at release commit
`8a2d04e7d2e393c035715520254bdd5955651873` and requires manager 0.10. The historical
0.9 migration evidence below remains evidence for the earlier checkpoint only.
Use the manager's `explicit-update` profile for new preparation, preserving fresh
source retrieval and manual acquisition. Explicit upgrade supplies a standalone
`update_policy` with mode `always` as an acquisition override. Until-released pin
retention is independent and application-owned. Register the returned catalog;
pass its combined flat UUID references to groups and revision-checked adoption.
Persist the expansion catalog, combined refs, and pin refs with pending intent
before group preparation, and reuse these exact inputs on uncertain retries.
Do not reproduce profile defaults in Python, install a managed application, or
add profile expansion to lookup. Credential, integrity and scope choices remain
independent. No new portable helper is needed: existing SDK methods own expansion
and existing Powerspec state and mutation boundaries own receipt persistence.

**Goals:** replace only the source/binary integration boundary while adding explicit consumer isolation and durable output ownership.
**Non-Goals:** no profile syntax conversion, builtin catalog rebuild redesign, new generic utilities, compatibility aliases, implicit fetch during lookup, service daemon, or Saucepan policy engine in Python.

## Decisions

### Dependencies and implementation structure

Pin the Python SDK Git-subdirectory dependency to 041e4f90634e6007b58054a59604396f8fbebd21 and update uv.lock during implementation. Keep Python >=3.12, Typer, Pydantic application validation and Zuu. Use a local source override only for development tests. Reuse SDK transport/serialization/errors; keep current feature-owned `sources.py` adapter and `saucepan_tool.py` bootstrap rather than introducing a cross-app adapter framework.

Portable utility assessment: subprocess bounds and payload lifecycle already belong to the SDK; release discovery/publication belongs to Zuu; a Saucepan-specific bounded ZIP downloader selects only the exact manager member using Python zipfile; bounded executable inspection already exists in utils.inspection. Consumer scope and SourceBinding mapping are application contracts. No new reusable helper is needed, so pspec-plan-utilities is not activated for speculative work. If implementation discovers a missing portable primitive, plan that bounded contract before dependent code.

### Explicit executable contract

App-owned path resolution replaces the removed SDK helper and preserves current shared ~/.saucepan/bin behavior and injected clients. Only ensure/upgrade paths may provision via Zuu. Lookup/status/hook inspection uses existing executable inspection under the caller's remaining deadline, with no install/update or directory creation.

Require tested 0.9 protocol and required commands, allowing version build metadata and rejecting 0.5/0.6. Change Zuu policy_id so old successful-check cache records cannot authorize a new contract. Keep 24-hour discovery checks and compatible-baseline fallback; an old executable is not a compatible fallback. Validate the actual manager member of the platform release archive (not the shim) before atomic publication. No Rust/keyring requirement for ordinary installs; basic integrity is the default.

### Identity and policy mapping

One application registration_key `powerspec` yields app.uuid; save/recover this stable identity through current API results. Each owning consumer uses an explicit scope derived from its canonical owning openspec/.pspec/config.toml path, not cwd or a mutable profile alias. Store the canonical identity and stable encoded scope in Powerspec-owned state. Repeated invocation reuses it; a moved/copied project requires explicit rebind, never aliases another scope silently.

Thread scope through workspace, direct status lookup, hook metadata lookup and upgrade. A global user installation has its own explicit scope. Profile aliases remain names in the effective bundle. Different consumers can track the same source independently and still share physical cache outputs.

Keep existing profile source declarations as application configuration. Translate provider/origin/reference into Source plus Selector at the SDK boundary; validate returned provenance against the requested source and selected commit. Normalize full-repository and covered relative views, preserve SourceBinding origin/reference/resolved_revision and use output UUID as current artifact identity. Do not reconstruct paths from cache layout or select a global latest source history record.

Policy definitions are registered immutable records. Use manual acquisition-update policy for ordinary ensured claims, explicit refresh policy for upgrade, revision and pin policies for retention, and explicit stale policy. Adopt new UUIDs rather than editing shared definitions. Explicit upgrade first adopts the new claim policy references at the observed app revision; otherwise the manager correctly rejects overlapping claims whose policy intent differs. Source and policy registration are explicit local administrative setup; acquisition and receipt reads remain bound to the app. Default app credentials_required=false, no public claim scope, no implicit full verification/keyring. Anonymous public source discovery, when needed, is separate from Powerspec's private scoped claim lookup.

### Lifecycle and retention

| Caller | Allowed work |
| --- | --- |
| status, sync, hook metadata, installed skill lookup | inspect existing compatible binary, saved identity, scoped query/claim/output/pin; no init/register/retrieve/acquire/update/pin/unpin |
| init/ensure | initialize absent store, idempotent registration/policies, acquire and pin only missing selected recipes; reuse existing exact bindings without refresh |
| upgrade | explicit refreshed candidates, validation, provisioning and committed consumer selection; remove obsolete installed copies only after the existing all-success boundary |

Use group acquisition with a generation-specific pin receipt when publishing new materializations; resolve all acquired paths from the pinned returned descriptors. A per-consumer manifest records selected source/output/claim/group/pin identities and current generation, not a copy of manager metadata or secrets. On uncertain mutation result reconcile the same registration key and expected revision. Metadata queries remain side-effect-free.

Do not let central claim movement select a new Powerspec binding before Powerspec validation succeeds. Stage candidate bindings separately, validate catalogs and selectors, then commit the local binding selection through existing state-writing conventions; failed candidates leave prior selection and pins intact. Consumer mutation uses a feature-owned exclusive lock around local receipt changes; crashed-writer locks require explicit PID verification before removal. Known rejected candidates are abandoned while retaining their pins; uncertain operations keep original keys for reconciliation. Upgrade publishes validated selections after skill/hook provisioning and obsolete ownership checks, before actual obsolete removal. Its obsolete-skill removal transaction remains owned by upgrading.py; Saucepan's group transaction does not roll back ZuAT copies.

Lookup uses the explicitly selected pinned generation, validates source/selector and relative containment from its authenticated group receipt, and reports missing/reclaimed/corrupt records without repair. Bound output inspect is unavailable in the current manager; receipt evidence supplies the exact selected source commit and intent without an unrestricted read fallback. Pins remain active across processes; read-only calls create no temporary pins. To avoid releasing a generation while another lookup reads it, prior generations are conservatively retained. Automatic historical-pin pruning is out of scope; explicit cleanup must establish no readers and must never alter another consumer's pins. This intentionally prefers bounded operational follow-up over a hidden race or invented read-side mutation.

### Structured errors and installation evidence

Replace stderr substring matching with domain codes from the pinned binary (for example access_denied and revision_conflict), preserving the existing ConfigurationError/MetadataUnavailable public distinction. Only documented missing-root/registration cases authorize initialization in ensure. Invalid records, denied access or unavailable protected keyrings do not authorize reset or unbound retry. Transport failures carry uncertainty through diagnostics and reconciliation.

Use injected clients for mapping tests, plus current real binary with local Git and disposable roots for init -> lookup -> changed origin -> lookup unchanged -> upgrade -> new selection. Add two-consumer same-source tests, contained subpaths, ambiguous source failures, stale policy, failed provisioning preserving old installed copies, receipt reconciliation and keyring-free operation. Assert zero mutating SDK calls for sync/status/hooks, including failure paths and inspection deadline exhaustion. Package tests install from declared immutable SDK source outside the workspace.

## Risks / Trade-offs

- [SourceBinding consumers assume old artifact structure] → update source tests/callers together; retain domain provenance fields without retaining a legacy protocol facade.
- [Powerspec consumes its own dependency] → use disposable development environment and fixtures, not the currently installed pspec or live config.
- [Source mutation succeeds before provisioning fails] → keep old local selection and old pins, report failure, reconcile staged receipts.
- [Retaining past generations consumes space] → report ownership for explicit cleanup; no automatic unpin without a reader-lifetime solution.
- [Upstream release unavailable] → source pin enables development; managed binary install acceptance waits for a tested obtainable 0.9 artifact.

## Migration Plan

Implement dependency and binary contract, then scoped bindings and structured errors, then ensure/upgrade pin publication and read-only lookups, then CLI/install verification and documentation. Use pspec-tdd for behavioral implementation as required by this repository. Old Saucepan record formats are unsupported; preserve them for user-directed recovery and never initialize over an incompatible live store. Rollback is separate consumer/environment restoration, not dual runtime support.

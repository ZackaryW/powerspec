# Design

## Context

See [proposal.md](proposal.md) for motivation. Powerspec already implements the original flat commands, but each Typer handler independently discovers consumers, builds catalogs, catches errors, and prints domain objects. `init` also composes profiles, acquires sources through Saucepan, installs skills through ZuAT, and registers hooks. The resulting public surface mixes user workflows with protocols intended to be called by agents.

The existing domain modules for consumers, profiles, sources, provisioning, synchronization, upgrading, temporary state, and skill resolution remain useful. This change reorganizes their application boundary rather than replacing those engines. It must preserve the two console-script aliases, the existing skill and hook protocol payloads, Git-root containment, profile exclusions, source ownership by Saucepan, and installation ownership by ZuAT.

## Goals / Non-Goals

**Goals:**

- Make the command tree explain the product lifecycle without prior architectural knowledge.
- Separate setup, synchronization, agent installation, and refresh into independently repeatable operations.
- Reuse one consumer/catalog loading path so commands agree on local resources, exclusions, and source availability.
- Return structured application results before rendering them as text or JSON.
- Preserve existing automation during a compatibility period.

**Non-Goals:**

- Reimplement Saucepan acquisition, ZuAT installation, OpenSpec initialization, or profile composition.
- Add an interactive wizard or prompt-driven compile-time configuration.
- Decide priority when a skill exists at both user and project scope; the target agent owns that lookup behavior.
- Add speculative framework layers beyond the use cases needed by the public commands.

## Decisions

### 1. Organize the CLI by audience and lifecycle

The root command exposes the human control plane (`init`, `status`, `sync`, `install`, `upgrade`, `doctor`, `config`) and the explicit `state` and `resolve` groups. `resolve` identifies machine-facing protocols, while `state` identifies temporal data maintenance. Historical `skill`, `hook`, and `flush` registrations call the same handlers with Typer's hidden flag.

Keeping every command flat was rejected because it gives protocol entrypoints the same prominence as common project workflows. Removing old commands immediately was rejected because installed hooks and external automation may still invoke them.

### 2. Split setup from installation

Initialization stops after establishing the Git-bounded OpenSpec and `.pspec` structure. Installation becomes the only ordinary command that may acquire missing selected sources, install skills, and reconcile the generic hook dispatcher. Upgrade refreshes already configured sources before using the same reconciliation path.

Keeping provisioning inside init was rejected because it makes repository setup depend on a chosen agent and live remote sources. A single all-purpose reconcile command was rejected because source refresh and OpenSpec context publication have materially different safety and review boundaries.

### 3. Use a shared application workspace loader

A small application service will resolve the owning consumer, open the bundled catalog, add `openspec/.pspec` as the private local source, and select a Saucepan resolver appropriate to the use case: lookup for read/sync, ensure for install, and refresh for upgrade. Commands receive a loaded workspace or a typed result instead of recreating those decisions.

This is intentionally smaller than a domain framework or dependency-injection container. Direct construction in every handler was rejected because it already produced inconsistent local-resource and failure behavior.

### 4. Validate sync completely before publication

Sync performs full composition and condition evaluation before calling the existing atomic publisher. Consumer-local resources participate in the catalog with local-first behavior. Missing remote resources are reported from lookup; sync never calls acquisition. The target YAML is therefore unchanged for every planning or validation failure.

Publishing partial guidance before reporting a missing selected skill was rejected because an error result must not silently mutate the effective OpenSpec instructions.

### 5. Use explicit result models and centralized presenters

Application use cases return dataclasses or Pydantic models containing paths, statuses, diagnostics, and nested outcomes. CLI adapters map known failures to exit codes and select a text or JSON presenter. Agent protocol renderers keep their current contracts and are not forced into the human result shape.

Printing throughout the domain layer was rejected because it prevents reliable JSON, makes tests assert formatting instead of behavior, and can produce contradictory success and error messages.

### 6. Keep configuration edits narrow and round-trip safe

Configuration inspection loads the owning committed `config.toml`. Profile updates use `tomlkit` to preserve comments, ordering, variables, exclusions, and unknown compatible fields while changing only the top-level profile. Clearing the selector leaves global profiles active. `config edit` delegates to `VISUAL`, then `EDITOR`, and reports a missing editor without guessing.

Rewriting configuration from a validated model was rejected because it would discard user formatting and forward-compatible fields.

## Utility Plan

### Atomic byte replacement

- **Purpose and portability:** Retain or extract the existing staging-and-`os.replace` mechanics used by synchronization as a generic helper for commands that must update a file without exposing partial bytes. Another configuration CLI could use the same contract for TOML updates.
- **Contract:** `replace_bytes(path: Path, content: bytes) -> bool` writes only when bytes differ, stages beside the target, flushes the file, replaces the destination atomically on the same filesystem, and returns whether content changed.
- **Effects and failures:** It writes one destination, removes its staging file after success or failure, and propagates a categorized write/replace error. It does not create parent directories or promise rollback after a successful replace.
- **Reuse:** The standard library supplies temporary files, flushing, and `os.replace`; no third-party package adds value. The current sync publisher already demonstrates the mechanics, so extraction avoids a second implementation.
- **Verification:** Use isolated filesystem fixtures for unchanged content, first write, replacement, injected replacement failure, original-byte preservation, and staging cleanup.

### Executable inspection

- **Purpose and portability:** Reuse a bounded subprocess inspection helper for `doctor` checks without embedding OpenSpec, Saucepan, or ZuAT policy. Another CLI could inspect its own prerequisites through the same operation.
- **Contract:** A helper accepts literal argv, cwd, timeout, and an optional version parser, then returns a small result containing availability, exit code, stdout/stderr, and parsed version when supplied.
- **Effects and failures:** It launches without a shell, never installs or repairs, bounds execution time, and distinguishes missing executable, timeout, nonzero exit, and unparseable version.
- **Reuse:** `shutil.which` and `subprocess.run` provide the required behavior. The existing `utils.processes` establishes safe literal-argv conventions but only accepts JSON, so a sibling result helper is justified instead of a wrapper around a dependency.
- **Verification:** Cover missing executable, successful version output, nonzero exit, timeout, and malformed version with controlled executables or patched process boundaries.

Application code supplies which files need replacement, which prerequisite commands matter, minimum supported versions, and how failures affect command status. Consumer ownership, profile composition, configuration semantics, and result presentation remain application concerns.

## Risks / Trade-offs

- **Compatibility aliases can linger indefinitely** → Mark them hidden, test equivalence, and document them only as migration support.
- **Status can accidentally acquire remote sources** → Give read-only use cases only the lookup resolver and test that acquisition is never called.
- **Install may leave successful resources when another item fails** → Report partial outcomes explicitly and make reruns convergent; preserve existing ZuAT ownership rather than attempting unsafe cross-tool rollback.
- **Configuration editing can race with another writer** → Compare observed bytes before atomic replacement and ask the user to rerun when the source changed.
- **A shared loader can become a policy container** → Keep resolver selection explicit per use case and return existing domain objects instead of adding a second model hierarchy.

## Migration Plan

1. Add result/presentation support and the shared workspace loader without changing command registration.
2. Make initialization setup-only and add installation using the extracted provisioning path.
3. Register the new command groups and inspection/configuration commands, then retain hidden aliases that call the same functions.
4. Make synchronization local-aware and preflight-complete before publication.
5. Update tests, help snapshots, examples, and README; validate both installed entrypoints.

Rollback can restore the previous command registrations and initialization orchestration because the consumer file formats, Saucepan materializations, and ZuAT-managed installations remain compatible.

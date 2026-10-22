# Design

## Context

The build hook already acquires twelve complete OpenSpec skill roots at an immutable revision and carries their snapshot in source distributions. The current pin is db2309783547a14e150dbcbfc19120e4028446c3; v1.14.3 resolves to c794978f4f8845ce59693373c9dd882ee776588c. Nine selected upstream entrypoints changed, including task source locations and pre-write glob containment. Local generated skills are a separate tracked surface under .agents/skills, identified as Codex by .openspec-target.

## Goals / Non-Goals

Keep both distribution and local workflow instructions aligned with the installed 1.14.3 CLI. Preserve complete supporting files, provenance, offline sdist rebuilds, and tools-none bootstrap. This does not redesign pspec-skill-bootstrap, install global skills, implement the separate routing proposal, bump Powerspec's version, or publish anything.

## Decisions

- Replace only the immutable upstream revision in the existing build declaration; reuse the current acquisition and snapshot APIs. A tag or runtime fetch would weaken reproducibility. No new utility is needed.
- Run the official `openspec update` command for the existing local Codex target and inspect its complete diff. Do not hand-copy upstream templates over generated entrypoints.
- Set both initialization and doctor's existing minimum to 1.14.3, with matching README and initialization guidance. This conservative floor matches the tested release whose skills require newer task-location output; preserving 1.13.2 would claim unverified compatibility. Existing consumer initialization still preserves its configuration.
- Validate version boundaries through existing public Python/CLI tests, then build a real wheel and sdist from the pinned public source, rebuild the wheel offline, compare all catalog paths and bytes, and exercise an installed wheel in an isolated consumer. Build fixtures alone do not establish released-source compatibility.

## Risks / Trade-offs

- New bundled instructions require CLI output fields absent from older releases → test rejection below the release floor and success at/above it.
- The CLI updater may refresh multiple configured generated surfaces → review its reported targets and diff; preserve authored configuration and unrelated work.
- Cached builds could conceal an old snapshot → use explicit fresh build output and inspect packaged provenance and entrypoint bytes.
- Offline wheel construction still needs cached build dependencies → distinguish missing dependency cache from snapshot/network behavior and prepare dependencies before the offline check.

## Migration Plan

Create a verified local checkpoint for CLI compatibility and the immutable bundle pin, then refresh generated skills and record distribution verification in another checkpoint. Users on older OpenSpec update their CLI explicitly. A rollback restores the previous pin and matching version checks together; no receipt or consumer migration is needed.

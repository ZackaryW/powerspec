# Proposal

## Why

Powerspec's implemented boundaries are mostly well factored, but its first release carries manifest features with no bundled consumers, duplicated low-level helpers, and tracked copies of resources owned by upstream projects. Simplifying those surfaces now keeps the public schema honest and makes packaged resources reproducible without maintaining duplicate authoring copies.

## What Changes

- **BREAKING** Introduce skill manifest version 2 and narrow composition to the two modes used by bundled skills: `after` and `replace`.
- **BREAKING** Remove unused manifest hint groups and make each input declare at most one prompt parser.
- Preserve the existing deterministic `after` and last-active-wins `replace` behavior while deleting combine, before-placement, hint-detection, and their dormant ordering rules.
- Reuse Powerspec's existing atomic publication and executable-inspection utilities instead of maintaining parallel implementations.
- Use the existing ruamel.yaml dependency for safe skill-frontmatter parsing and remove Powerspec's direct PyYAML dependency.
- Retire hidden legacy CLI aliases after integrations use the grouped `resolve` and `state` command surfaces.
- Replace tracked copies of upstream OpenSpec skills with one pinned build-source declaration. Materialize that source through Hatch build staging so wheels remain self-contained without making `.pspec/skills` a second upstream source of truth.

## Capabilities

### New Capabilities

- `package-distribution`: Defines reproducible bundling of externally owned resources through a pinned Hatch build source.

### Modified Capabilities

- `skill-content-resolution`: Narrows the v1 skill manifest to used composition and prompt behavior while preserving deterministic resolution.

## Impact

- Skill manifests using `before`, `combine`, `[[hint]]`, `default_hint`, or multiple prompt parsers must migrate before upgrading.
- `src/powerspec/skills.py`, temporary-state publication, executable inspection, skill catalog parsing, CLI registration, tests, and documentation will shrink.
- Builds must resolve the declared OpenSpec revision while producing the sdist, preserve its selected skills, license, and provenance in the artifact, and rebuild the wheel from that sdist without another network fetch.
- The grouped CLI, profile/context/trait model, source precedence, hook adapters, Markdown ATX-section contract, and transactional upgrade behavior remain unchanged.

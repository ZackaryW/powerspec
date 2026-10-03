# Proposal

## Why

Powerspec's implemented boundaries are mostly well factored, but its first release carries manifest features with no bundled consumers, duplicated low-level helpers, and Git-hosted runtime dependencies that make installation less predictable than the domain requires. Simplifying those surfaces now keeps the public schema honest and makes packaged deployments independent of a source checkout.

## What Changes

- **BREAKING** Introduce skill manifest version 2 and narrow composition to the two modes used by bundled skills: `after` and `replace`.
- **BREAKING** Remove unused manifest hint groups and make each input declare at most one prompt parser.
- Preserve the existing deterministic `after` and last-active-wins `replace` behavior while deleting combine, before-placement, hint-detection, and their dormant ordering rules.
- Reuse Powerspec's existing atomic publication and executable-inspection utilities instead of maintaining parallel implementations.
- Use the existing ruamel.yaml dependency for safe skill-frontmatter parsing and remove Powerspec's direct PyYAML dependency.
- Retire hidden legacy CLI aliases after integrations use the grouped `resolve` and `state` command surfaces.
- Replace Git URL runtime dependencies with versioned Saucepan SDK, ZuAT, and Zuu distributions from a configured package index, and add locked/no-source release verification for the Powerspec wheel.

## Capabilities

### New Capabilities

- `package-distribution`: Defines reproducible, source-independent packaging and installation of Powerspec and its Python runtime dependencies.

### Modified Capabilities

- `skill-content-resolution`: Narrows the v1 skill manifest to used composition and prompt behavior while preserving deterministic resolution.

## Impact

- Skill manifests using `before`, `combine`, `[[hint]]`, `default_hint`, or multiple prompt parsers must migrate before upgrading.
- `src/powerspec/skills.py`, temporary-state publication, executable inspection, skill catalog parsing, CLI registration, tests, and documentation will shrink.
- Release preparation must publish or otherwise make versioned Saucepan SDK, ZuAT, and Zuu wheels available through the configured package index before Powerspec removes Git references.
- The grouped CLI, profile/context/trait model, source precedence, hook adapters, Markdown ATX-section contract, and transactional upgrade behavior remain unchanged.

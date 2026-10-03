# Proposal

## Why

The TDD source and rendered Python example describe a working model, but pspec skill is still a placeholder. Implement the read-only lookup and composition path so an agent can receive only the selected procedure with real configured inputs.

## What Changes

- Resolve the explicitly selected agent's installed skill through ZuAT's read-only lookup, with optional host-reported `--selected PATH` evidence when native rules cannot distinguish installed copies.
- Parse skill-local manifests, evaluate reachable inputs and hints, and assemble dynamic before/after/replace/combine sections.
- Return plain Markdown or opt-in JSON with distinct unsupported, pending, resolved, and failed outcomes.
- Preserve the bootstrap exemption, explicit change identity, native skill selection, and uv run pytest defaults.
- Transition the CLI scaffold contract to distinguish remaining placeholders from commands implemented by their capability specs; implement only skill here.

## Capabilities

### New Capabilities

- `skill-content-resolution`: Manifest parsing, selected inputs, guarded resources, deterministic section composition, and atomic read-only output.
- `skill-bootstrap`: Lookup convention, native selection, pending answers, and Markdown/JSON command results.

### Modified Capabilities

- `cli-scaffold`: Honest per-command readiness and side-effect boundaries as placeholders are replaced incrementally.

## Impact

Depends on establish-profile-consumer-resolution. Extends src/powerspec/cli/skill.py and adds the resolver and explicit-agent inspection adapter. Uses disposable installed-skill fixtures, not real-home provisioning. No init, hook, remote acquisition, sync, or flush implementation.

Completion means pspec skill pspec-tdd --agent <agent> returns the reviewed Python Markdown from an isolated installed skill, and pending/null/error cases are verified. Packaging and automatic hook discovery can follow independently of this first usable command.

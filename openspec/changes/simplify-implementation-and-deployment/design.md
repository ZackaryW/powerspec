# Design

## Context

The implemented product is a small Python CLI whose custom code owns domain-specific profile composition, source policy, hook adaptation, OpenSpec publication, and skill document resolution. Mature libraries already cover validation, editable TOML, round-trip YAML, CLI parsing, managed executable delivery, agent asset ownership, and remote materialization. The remaining complexity is concentrated in unused version 1 manifest features, repeated low-level helpers, and runtime dependencies expressed as pinned Git URLs.

The current bundled manifests use `after` and `replace`; none uses `before`, `combine`, or hints. The test suite passes before this change, providing a regression baseline. See proposal.md and the two delta specifications for the behavioral scope.

## Goals / Non-Goals

**Goals:**

- Make the manifest schema express only behavior exercised by shipped skills.
- Preserve deterministic dynamic content and strict diagnostics while reducing composition states.
- Reuse existing project utilities and dependencies where they already satisfy the required contract.
- Make published installation independent of Git and repository availability.

**Non-Goals:**

- Replacing profile composition, source precedence, hook adapters, or transactional upgrade policy with generic frameworks.
- Broadening Markdown support beyond the documented unique ATX-heading contract.
- Vendoring Saucepan SDK, ZuAT, or Zuu into Powerspec.
- Changing the native Saucepan executable's Zuu-managed lifecycle.

## Decisions

### Introduce manifest version 2 as a clean schema break

Version 2 retains scalar inputs, defaults, one optional prompt, conditions, `after`, `replace`, source-section selection, and single-pass substitution. It removes hints, `before`, `combine`, and parser arrays. The loader reports a migration diagnostic for version 1 instead of maintaining two composition engines. Bundled manifests migrate in the same release.

Keeping the version number while changing accepted fields would make cached or externally installed manifests fail unpredictably. Supporting both versions would preserve most code the audit intends to remove.

### Keep the focused ATX section scanner

The section contract needs exact ATX headings, fence exclusion, original character offsets, and deterministic slicing. A CommonMark parser would broaden syntax and still require Powerspec-specific selection and composition logic. The existing focused scanner therefore remains, with the composition pass simplified around only `after` and `replace`.

### Reuse internal publication and inspection utilities

Temporary-state cleanup validates the candidate and then calls the existing atomic byte replacement helper. OpenSpec initialization and doctor checks share executable inspection and version parsing where their policies overlap. Application-specific error messages and bootstrap commands remain with their owning modules.

This uses existing tested helpers; no new generic utility or third-party process framework is introduced.

### Consolidate YAML APIs on ruamel.yaml

Skill frontmatter uses a safe, non-round-trip ruamel.yaml loader while OpenSpec configuration retains its round-trip loader. This removes Powerspec's direct use of PyYAML. PyYAML may remain transitively installed while ZuAT requires it, but Powerspec no longer depends on that implementation detail.

### Publish Python integrations as ordinary package artifacts

Saucepan SDK, ZuAT, and Zuu are released as versioned Python distributions to the configured index before Powerspec switches its metadata. Powerspec declares compatible version ranges, while the repository lock records the tested concrete graph. Release CI builds with source overrides disabled, inspects wheel metadata, and performs a clean tool installation smoke test.

The alternative of bundling those projects into the Powerspec wheel would blur ownership and release cadence. Retaining Git URLs would keep builds tied to GitHub and a Git executable even though revisions are pinned.

### Remove compatibility aliases only after integrations migrate

The grouped `resolve skill`, `resolve hook`, and `state clear` commands remain canonical. Existing documentation and managed hook payloads migrate first; hidden aliases are removed in the same release only after repository searches and integration tests show no remaining caller.

## Risks / Trade-offs

- **External version 1 manifests stop resolving** → Emit a direct migration diagnostic and document the mechanical field changes before release.
- **A removed hint later proves useful** → Reintroduce a concrete detector in a later schema version only with a real consumer and acceptance cases.
- **Dependency wheels are not ready together** → Keep the Git-reference change unmerged until all three compatible artifacts are published and installable from the target index.
- **Removing a direct PyYAML dependency does not immediately shrink installations** → Record that ZuAT still supplies it transitively and avoid claiming a distribution-size reduction until that dependency changes upstream.
- **Release locks can hide overly narrow metadata** → Test both the locked repository and a clean wheel installation against declared compatibility ranges.

## Migration Plan

1. Publish compatible Saucepan SDK, ZuAT, and Zuu distributions and verify their public APIs used by Powerspec.
2. Implement manifest version 2 and migrate bundled skill manifests and documentation.
3. Simplify composition, prompt resolution, temporary publication, executable inspection, and YAML parsing with focused regression tests.
4. Update dependency metadata and lock, then build with source overrides disabled and install the wheel in a clean environment.
5. Migrate managed command invocations and remove hidden aliases after no callers remain.
6. Roll back by restoring the prior Powerspec release; do not publish version 2 metadata until its bundled skills and dependency artifacts pass the release gate.

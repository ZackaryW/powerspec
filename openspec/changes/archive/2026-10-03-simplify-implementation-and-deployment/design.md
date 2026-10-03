# Design

## Context

The implemented product is a small Python CLI whose custom code owns domain-specific profile composition, source policy, hook adaptation, OpenSpec publication, and skill document resolution. Mature libraries already cover validation, editable TOML, round-trip YAML, CLI parsing, managed executable delivery, agent asset ownership, and remote materialization. The remaining complexity is concentrated in unused version 1 manifest features, repeated low-level helpers, and duplicated upstream resources.

The current bundled manifests use `after` and `replace`; none uses `before`, `combine`, or hints. Upstream OpenSpec skills are also copied into `.pspec/skills` and then force-included into the wheel, leaving the repository to maintain a second copy of content already owned by an immutable upstream revision. The test suite passes before this change, providing a regression baseline. See proposal.md and the two delta specifications for the behavioral scope.

## Goals / Non-Goals

**Goals:**

- Make the manifest schema express only behavior exercised by shipped skills.
- Preserve deterministic dynamic content and strict diagnostics while reducing composition states.
- Reuse existing project utilities and dependencies where they already satisfy the required contract.
- Keep upstream skill ownership declarative while producing self-contained Python artifacts through Hatch.

**Non-Goals:**

- Replacing profile composition, source precedence, hook adapters, or transactional upgrade policy with generic frameworks.
- Broadening Markdown support beyond the documented unique ATX-heading contract.
- Changing the pinned Git dependency model for Saucepan SDK, ZuAT, or Zuu.
- Changing the native Saucepan executable's Zuu-managed lifecycle.
- Turning packaged builtin OpenSpec skills into runtime profile sources that `pspec init` must fetch.

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

### Materialize upstream OpenSpec skills through the Hatch build boundary

Declare the OpenSpec repository, immutable commit, selected `skills/` paths, and license path in the custom Hatch hook configuration. `hatch_build.py` reads that declaration and uses the available versioned Zuu build integration to materialize a contained staging tree. During Hatch initialization it maps the validated skills into `powerspec/_resources/catalog/skills` through `build_data["force_include"]`; the repository no longer tracks those upstream skill directories under `.pspec/skills`.

For an sdist build, include the resolved tree plus a generated manifest containing the declared revision and content digests. When building a wheel from that sdist, validate and reuse the carried tree without contacting the network. A direct wheel build from a checkout may materialize the same pinned declaration, but both paths must yield the same resource paths and bytes. Clean hook staging after the build and reject absent, incomplete, escaping, or mismatched source content.

This is packaging-source configuration, not a normal Powerspec profile `[[source]]`. Runtime source declarations would make initialization network-dependent and preserve external identities instead of delivering the reviewed builtin catalog. Static `force-include` from `.agents/skills` was also rejected because those files govern this checkout, can differ from the release revision, and would merely choose another mutable repository copy as the package source.

### Remove compatibility aliases only after integrations migrate

The grouped `resolve skill`, `resolve hook`, and `state clear` commands remain canonical. Existing documentation and managed hook payloads migrate first; hidden aliases are removed in the same release only after repository searches and integration tests show no remaining caller.

## Risks / Trade-offs

- **External version 1 manifests stop resolving** → Emit a direct migration diagnostic and document the mechanical field changes before release.
- **A removed hint later proves useful** → Reintroduce a concrete detector in a later schema version only with a real consumer and acceptance cases.
- **Removing a direct PyYAML dependency does not immediately shrink installations** → Record that ZuAT still supplies it transitively and avoid claiming a distribution-size reduction until that dependency changes upstream.
- **Release builds now require the pinned OpenSpec source when producing an sdist** → Resolve only the immutable revision, fail closed, and carry the validated snapshot in the sdist so downstream wheel builds remain offline.
- **Editable development could observe stale generated resources** → Make the build hook validate the generated manifest and content digests, and test resource discovery through the editable/build path rather than falling back to copied upstream directories.

## Migration Plan

1. Implement manifest version 2 and migrate bundled skill manifests and documentation.
2. Simplify composition, prompt resolution, temporary publication, executable inspection, and YAML parsing with focused regression tests.
3. Add the pinned OpenSpec build-source declaration and custom Hatch staging hook, then remove the tracked upstream skill copies from `.pspec/skills`.
4. Build the sdist, rebuild its wheel offline, and compare packaged resources with a direct wheel.
5. Migrate managed command invocations and remove hidden aliases after no callers remain.
6. Roll back by restoring the prior Powerspec release if the bundled skills or build-source snapshot fail validation.

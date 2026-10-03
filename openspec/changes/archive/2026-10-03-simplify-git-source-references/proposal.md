# Proposal

## Why

Remote skill declarations currently repeat both the Git-source namespace and the source alias even though the profile already declares that alias with an exact repository recipe. Allowing `zmem/skills/*` to mean “select from declared source `zmem`” keeps authored configuration concise while retaining explicit acquisition and provenance.

## What Changes

- Replace authored `@gitsource/<alias>/<path-pattern>` skill selectors with `<alias>/<path-pattern>` selectors whose first segment must match an effective `[[source]]` declaration.
- Normalize the shorthand into Powerspec's structured remote-source identity before selection, arming, provisioning, and diagnostics.
- Preserve `@builtin/<name>` and other qualified catalog references for packaged or registered catalog resources.
- Reject unknown source aliases, malformed paths, and ambiguous source/resource interpretations without deriving repository coordinates.
- Migrate bundled profiles, examples, documentation, and tests to the shorthand.
- **BREAKING**: authored `@gitsource/...` selectors are no longer the supported profile syntax.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `remote-sources`: Change direct Git skill-path selection to use a declared source alias as the first segment without an `@gitsource` namespace.
- `profile-skill-bundles`: Permit source-relative skill selectors alongside qualified packaged/catalog skill references while preserving strict identity and composition behavior.

## Impact

This affects profile validation, catalog selection and canonical identities, condition arming, provisioning provenance, bundled external-source profiles, remote-source documentation, and compatibility tests. Saucepan recipes, full-repository acquisition, ZuAT installation names, and the remote repository coordinates remain unchanged.

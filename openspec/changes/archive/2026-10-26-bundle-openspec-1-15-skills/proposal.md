# Proposal

## Why

OpenSpec v1.15.0 fixes `/opsx:verify` so a REMOVED requirement is matched to its baseline by exact normalized name, the same rule OpenSpec uses when applying REMOVED blocks. With the bundled v1.14.3 snapshot, a similarly named replacement requirement can be mistaken for the removed one. This is the only change to a bundled skill between v1.14.3 and v1.15.0. Nothing in the bundled skills or in Powerspec's own OpenSpec invocations needs a 1.15 CLI feature. Raising the CLI floor together with the snapshot would force every user to upgrade OpenSpec without any functional gain.

## What Changes

- Pin the bundled OpenSpec workflow snapshot to the v1.15.0 release commit `8e0288df12d401b0e183e2f47254d22528c1dffb` (previously v1.14.3 `c794978`). Only `openspec-verify-change` changes content; the other eleven skill roots are byte-identical.
- Keep the fresh-bootstrap and doctor CLI floor at OpenSpec 1.14.3.
- Define the floor as the oldest CLI release compatible with the bundled skills and Powerspec's OpenSpec invocations, not the snapshot's release number. The floor is raised only when a bundled skill or Powerspec invocation depends on newer CLI behavior.
- Update compatibility documentation to state the snapshot and the floor separately.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `package-distribution`: the CLI compatibility floor is decoupled from the bundled snapshot release, which becomes v1.15.0 while the floor stays 1.14.3.

## Impact

- Build: `pyproject.toml` `[tool.hatch.build.hooks.custom.source].revision`; a rebuilt distribution is required to ship the new snapshot.
- Docs: `docs/packaged-resources.md` (snapshot and floor stated separately); README and `docs/initialization.md` floor wording stays 1.14.3.
- Code: none; bootstrap and doctor checks keep 1.14.3.
- Not breaking: users on OpenSpec 1.14.3 through 1.15.x keep working.

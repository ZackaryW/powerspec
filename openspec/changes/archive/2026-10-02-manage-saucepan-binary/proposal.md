# Proposal

## Why

Powerspec depends on the Saucepan SDK for remote source lookup, but a fresh machine currently fails when the shared Saucepan executable is absent. Zuu already provides a validated, atomic release-binary lifecycle, so Powerspec should use that boundary instead of requiring a separate manual install step.

## What Changes

- Ensure a Saucepan executable compatible with the installed Saucepan SDK before constructing the default remote-source client.
- Use Zuu's managed-release lifecycle for platform asset selection, staged validation, atomic installation or upgrade, freshness checks, and compatible stale fallback.
- Keep injected Saucepan clients independent of the managed executable for tests and explicit integrations.
- Document the automatic tool lifecycle and its failure behavior.

## Capabilities

### New Capabilities

- `managed-saucepan-binary`: Automatic installation and compatible upgrade of the Saucepan executable used by Powerspec remote sources.

## Impact

This change builds on `integrate-remote-sources`. It adds no Powerspec-specific downloader and does not change source registration, materialization, selection, or skill installation semantics.

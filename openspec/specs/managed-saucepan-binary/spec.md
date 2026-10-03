# Managed Saucepan Binary Specification

## Purpose

Ensure Powerspec can obtain and maintain a compatible Saucepan executable for remote-source operations without requiring a separate manual installation step.

## Requirements

### Requirement: Default source clients ensure a compatible Saucepan executable

Before constructing its default Saucepan SDK client, Powerspec SHALL use Zuu's managed-release lifecycle to ensure the SDK shared executable path contains a validated Saucepan release on the explicitly supported 0.5 or 0.6 CLI protocol lines. Powerspec SHALL create the shared executable's parent directory when needed, select the current platform asset from official Saucepan GitHub releases, probe its version, validate its command surface, and publish it atomically.

#### Scenario: Shared executable is absent
- **WHEN** a normal Powerspec command first needs the default Saucepan source client and no shared executable exists
- **THEN** a compatible validated release is installed at the SDK shared executable path before the client is used

#### Scenario: No remote source is resolved
- **WHEN** a command constructs a catalog but its effective bundle requires no Saucepan identity
- **THEN** the managed executable lifecycle is not invoked

#### Scenario: Compatible update is available
- **WHEN** the cached release check is stale and a newer compatible release is available
- **THEN** Powerspec validates and atomically publishes the newer executable before using the default client

### Requirement: Managed checks preserve usable tools and avoid needless discovery

Powerspec SHALL cache successful managed release checks for 24 hours. A fresh cache entry for the same destination, release source, policy, and installed version SHALL reuse the executable without remote discovery. A discovery or upgrade failure SHALL preserve a compatible installed executable according to Zuu's fallback contract. If no compatible executable can be produced, Powerspec SHALL report a configuration error and SHALL NOT claim the source operation succeeded.

#### Scenario: Fresh compatible executable
- **WHEN** the installed executable and matching successful check are younger than 24 hours
- **THEN** Powerspec reuses the executable without GitHub release discovery

#### Scenario: Upgrade fails with a compatible baseline
- **WHEN** release discovery, download, validation, or publication fails and a compatible executable was already installed
- **THEN** Powerspec uses that baseline without replacing it with partial or invalid content

#### Scenario: Initial installation fails
- **WHEN** no compatible executable exists and the managed lifecycle cannot produce one
- **THEN** Powerspec reports the installation failure before attempting a Saucepan source operation

### Requirement: Explicit clients bypass managed provisioning

Powerspec SHALL use an explicitly supplied Saucepan-compatible client without installing, upgrading, probing, or otherwise managing the shared executable.

#### Scenario: Isolated client is supplied
- **WHEN** a caller constructs `SaucepanSources` with an explicit client
- **THEN** source lookup and acquisition use that client without invoking the managed binary lifecycle

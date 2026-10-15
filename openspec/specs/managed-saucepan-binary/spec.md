# Managed Saucepan Binary Specification

## Purpose

Ensure Powerspec can obtain and maintain a compatible Saucepan executable for remote-source operations without requiring a separate manual installation step.

## Requirements

### Requirement: Default source clients ensure a compatible Saucepan executable
Before constructing a default client for an operation authorized to materialize or upgrade remote sources, Powerspec SHALL ensure its configured shared executable contains a validated release on the explicitly supported 0.10 protocol line. Executable path resolution SHALL be owned by Powerspec and independent of the client package. Powerspec SHALL create the parent directory only in that authorized provisioning path, select the host manager asset from official releases, probe its version and required command surface, and publish it atomically using the established managed-release lifecycle. SDK package version and binary protocol version SHALL be tracked independently. The package SHALL declare an immutable current client dependency and SHALL NOT retain a legacy wire fallback.

Read-only lookup, status and hook inspection SHALL inspect an existing executable within their remaining deadline without provisioning, release discovery or filesystem initialization.

#### Scenario: Shared executable is absent
- **WHEN** an authorized materialization operation first needs the default client and the shared executable is absent
- **THEN** a compatible validated manager binary is installed before the client performs source operations

#### Scenario: No remote source is resolved
- **WHEN** a command constructs a catalog whose effective bundle needs no Saucepan identity
- **THEN** the managed executable lifecycle is not invoked

#### Scenario: Compatible update is available
- **WHEN** an authorized provisioning path has a stale check and a newer compatible release is available
- **THEN** Powerspec validates and atomically publishes that executable before using the default client

#### Scenario: Read-only operation has no compatible binary
- **WHEN** status, sync or hook metadata inspection cannot find a compatible installed executable
- **THEN** it reports unavailable metadata within its deadline without downloading, replacing or initializing anything

#### Scenario: Old check cache exists
- **WHEN** a previous successful binary check belongs to the 0.5/0.6 compatibility policy
- **THEN** it does not establish compatibility with the new protocol

#### Scenario: Installed consumer outside the checkout
- **WHEN** a Powerspec distribution is installed with its declared current client dependency and supplied a compatible executable
- **THEN** remote-source operations work without a Saucepan development checkout, Rust toolchain or mandatory native keyring

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

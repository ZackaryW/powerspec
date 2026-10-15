# Managed Saucepan Binary Delta

## MODIFIED Requirements

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

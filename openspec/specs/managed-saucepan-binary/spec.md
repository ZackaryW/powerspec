# Managed Saucepan Binary Specification

## Purpose

Ensure Powerspec can obtain and maintain a compatible Saucepan executable for remote-source operations without requiring a separate manual installation step.

## Requirements

### Requirement: Default source clients ensure a compatible Saucepan executable
Before constructing a default client for an operation authorized to materialize remote sources, Powerspec SHALL ensure that the default shared launcher belongs to a ready Saucepan-managed installation supporting the explicitly pinned setup/SDK protocol. Missing installations SHALL use the verified official installer and Saucepan setup contract. Powerspec SHALL not publish a raw manager, construct Saucepan policies/receipts, adopt an occupant or independently replace the launcher. The provider SHALL own root initialization, application/claim/binding publication, shim ownership and recovery. SDK package version and binary protocol version SHALL remain independent, and the package SHALL declare an immutable compatible SDK dependency without a legacy wire fallback.

Read-only lookup, status and hook inspection SHALL inspect an existing executable and applicable setup status within their remaining deadline without provisioning, release discovery, setup, migration or filesystem initialization. Default unmanaged/incomplete installations SHALL report actionable diagnostics, preserving existing files. Bundled-only operations SHALL not trigger installation.

#### Scenario: Shared executable is absent
- **WHEN** an authorized materialization operation first needs the default client and no installation exists
- **THEN** Powerspec invokes the verified official setup route and creates the source client only after complete managed publication and compatibility verification

#### Scenario: No remote source is resolved
- **WHEN** a command constructs a catalog whose effective bundle needs no Saucepan identity
- **THEN** the managed executable setup lifecycle is not invoked

#### Scenario: Compatible update is available
- **WHEN** a newer compatible release exists while a ready compatible installation is already present
- **THEN** Powerspec reuses the installation without discovery, download or shared self-update

#### Scenario: Read-only operation has no compatible binary
- **WHEN** status or hook metadata inspection cannot find a ready compatible default installation
- **THEN** it reports unavailable metadata within its deadline without downloading, replacing or initializing anything

#### Scenario: Old check cache exists
- **WHEN** a previous Powerspec release-check cache exists beside a default raw manager
- **THEN** it establishes neither managed ownership nor migration authority and remains untouched

#### Scenario: Installed consumer outside the checkout
- **WHEN** an installed Powerspec distribution uses its pinned setup-capable SDK and a ready compatible manager
- **THEN** remote-source operations work without a Saucepan checkout, Rust toolchain or mandatory keyring for a basic store

### Requirement: Managed checks preserve usable tools and avoid needless discovery
Powerspec SHALL reuse ready compatible installations without its own 24-hour manager release-discovery/update cycle. A failed inspection, dependency setup or explicit external update SHALL not authorize replacing a shared launcher or fabricating success. If compatibility/readiness cannot be established, Powerspec SHALL report the observed state and provider retry/update instructions before attempting the source operation. Manager self-update SHALL remain explicit and provider-owned; Powerspec upgrade SHALL continue to refresh selected resources without implicitly updating the manager. Old check-cache files SHALL not drive writes and SHALL not be deleted merely because they are obsolete.

#### Scenario: Fresh compatible executable
- **WHEN** a ready compatible managed launcher is available
- **THEN** Powerspec reuses it without release discovery independently of cache age

#### Scenario: Upgrade fails with a compatible baseline
- **WHEN** a provider update fails and its managed contract retains the prior compatible installation
- **THEN** later Powerspec inspection can reuse that verified baseline without writing a replacement or claiming the update succeeded

#### Scenario: Initial installation fails
- **WHEN** official setup cannot complete a compatible installation
- **THEN** Powerspec reports the setup outcome and operation identity before attempting source acquisition, without retrying the mutation automatically

### Requirement: Explicit clients bypass managed provisioning

Powerspec SHALL use an explicitly supplied Saucepan-compatible client without installing, upgrading, probing, or otherwise managing the shared executable.

#### Scenario: Isolated client is supplied
- **WHEN** a caller constructs `SaucepanSources` with an explicit client
- **THEN** source lookup and acquisition use that client without invoking the managed binary lifecycle

### Requirement: Official installer invocation preserves authorization and receipts
Powerspec SHALL stage an official installer identified by immutable release evidence and verified checksum outside the store, then invoke it with literal arguments, selected root/tag and a stable operation ID. It SHALL not silently choose latest, evaluate unverified downloaded text, bypass host execution policy or substitute raw publication when prerequisites are missing. Source lifecycle authorization SHALL permit first setup but SHALL not imply consent to migrate an existing file. Complete setup SHALL be checked through the returned launcher and status contract; recorded pending/failure/conflict and uncertain transport outcomes SHALL retain their operation identities and diagnostics without automatic retry. Setup progress SHALL remain on stderr and protocol stdout SHALL retain its existing representation.

#### Scenario: Response lost after setup might have committed
- **WHEN** installer invocation loses its response after possible execution
- **THEN** Powerspec reports uncertainty with the original operation/root rather than retrying under a new ID or claiming success

#### Scenario: Missing shell prerequisite
- **WHEN** the official installer cannot run on the host
- **THEN** Powerspec reports how to use the supported official setup route and does not publish a raw manager as fallback

### Requirement: Standalone overrides and explicit migration remain distinct
An explicit POWERSPEC_SAUCEPAN executable override SHALL be inspected for protocol compatibility and used without installing, updating, adopting or requiring managed ownership of that file. Explicit SDK clients SHALL retain their existing bypass. An unmanaged manager at the default shared path SHALL instead require the provider's explicit migration route or a separately selected standalone override. Powerspec SHALL not pass migration consent based on filename, version, cache records, init or upgrade alone. A completed provider migration SHALL be consumed through its verified managed launcher; backups and migration receipts remain provider-owned.

#### Scenario: Compatible explicit override
- **WHEN** a caller selects a standalone executable explicitly
- **THEN** source operations use it without provisioning or changing that executable

#### Scenario: Existing default raw manager
- **WHEN** init encounters the existing default raw manager without explicit migration
- **THEN** it preserves that file and reports the provider migration command and observed digest without executing displacement

#### Scenario: Provider migration completed
- **WHEN** the user explicitly completes Saucepan's verified migration and reruns Powerspec
- **THEN** Powerspec verifies and uses the owned launcher without deleting backups or replacing it through Zuu

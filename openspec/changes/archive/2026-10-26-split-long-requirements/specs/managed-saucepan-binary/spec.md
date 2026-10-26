## MODIFIED Requirements

### Requirement: Default source clients ensure a compatible Saucepan executable
Before constructing a default client for an operation authorized to materialize remote sources, Powerspec SHALL ensure the default shared launcher belongs to a ready Saucepan-managed installation supporting the pinned setup/SDK protocol. Missing installations SHALL use the verified official installer and Saucepan setup contract. Powerspec SHALL NOT publish a raw manager, construct Saucepan policies or receipts, adopt an occupant, or independently replace the launcher.

#### Scenario: Shared executable is absent
- **WHEN** an authorized materialization operation first needs the default client and no installation exists
- **THEN** Powerspec invokes the verified official setup route and creates the source client only after complete managed publication and compatibility verification

#### Scenario: Compatible update is available
- **WHEN** a newer compatible release exists while a ready compatible installation is already present
- **THEN** Powerspec reuses the installation without discovery, download or shared self-update

#### Scenario: Occupant is not adopted
- **WHEN** an unmanaged file occupies the default launcher path
- **THEN** Powerspec neither adopts nor replaces it outside the provider's migration route

#### Scenario: No remote source is resolved
- **WHEN** a command constructs a catalog whose effective bundle needs no Saucepan identity
- **THEN** the managed executable setup lifecycle is not invoked

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
Powerspec SHALL reuse ready compatible installations without its own 24-hour release-discovery/update cycle. Failed inspection, dependency setup or external update SHALL NOT authorize replacing a shared launcher or fabricating success; when compatibility cannot be established, Powerspec SHALL report the observed state and provider instructions before the source operation. Manager self-update SHALL remain explicit and provider-owned, and Powerspec upgrade SHALL NOT update the manager.

#### Scenario: Fresh compatible executable
- **WHEN** a ready compatible managed launcher is available
- **THEN** Powerspec reuses it without release discovery independently of cache age

#### Scenario: Upgrade fails with a compatible baseline
- **WHEN** a provider update fails and its managed contract retains the prior compatible installation
- **THEN** later Powerspec inspection can reuse that verified baseline without writing a replacement or claiming the update succeeded

#### Scenario: Initial installation fails
- **WHEN** official setup cannot complete a compatible installation
- **THEN** Powerspec reports the setup outcome and operation identity before attempting source acquisition, without retrying the mutation automatically

#### Scenario: Upgrade leaves the manager alone
- **WHEN** pspec upgrade refreshes selected resources
- **THEN** it does not update the Saucepan manager

#### Scenario: Obsolete check cache stays inert
- **WHEN** check-cache files from an earlier Powerspec release exist
- **THEN** they drive no writes and are not deleted merely because they are obsolete

### Requirement: Official installer invocation preserves authorization and receipts
Powerspec SHALL stage an official installer identified by immutable release evidence and a verified checksum outside the store, and invoke it with literal arguments, the selected root and tag, and a stable operation ID. It SHALL NOT silently choose latest, evaluate unverified downloaded text, bypass host execution policy, or substitute raw publication when prerequisites are missing. Setup progress SHALL stay on stderr, leaving protocol stdout unchanged.

#### Scenario: Missing shell prerequisite
- **WHEN** the official installer cannot run on the host
- **THEN** Powerspec reports how to use the supported official setup route and does not publish a raw manager as fallback

#### Scenario: Installer is pinned and verified
- **WHEN** a release newer than the pinned installer tag exists
- **THEN** Powerspec stages the pinned tag's installer, verifies its checksum, and does not choose the latest release

#### Scenario: Setup output keeps protocol stdout clean
- **WHEN** official setup reports progress during a Powerspec command
- **THEN** that progress appears on stderr and protocol stdout keeps its existing representation

#### Scenario: Response lost after setup might have committed
- **WHEN** installer invocation loses its response after possible execution
- **THEN** Powerspec reports uncertainty with the original operation/root rather than retrying under a new ID or claiming success

#### Scenario: Forced initialization migrates a supported raw manager
- **WHEN** init --force needs the default manager and Saucepan accepts the observed unmanaged installation for verified migration
- **THEN** Powerspec invokes the verified official installer with explicit migration consent and the observed digest, and proceeds only after complete managed publication and reinspection
- **AND** provider-verified backups and recovery receipts remain available

#### Scenario: Candidate changes after inspection
- **WHEN** the raw executable changes after its digest is observed but before migration
- **THEN** provider verification rejects displacement and init reports failure without source acquisition or an unrestricted retry

#### Scenario: Forced migration is rejected
- **WHEN** provider preflight rejects a link, unknown sidecar, unsupported store, binary-only root, or busy file
- **THEN** init --force preserves the provider diagnostic and does not relocate files, bypass checks, or claim migration success

#### Scenario: Forced initialization encounters interrupted setup
- **WHEN** an earlier setup is pending, conflicting, or has an uncertain result
- **THEN** init --force directs recovery of the original provider operation without automatically replaying it or creating a replacement migration identity

### Requirement: Standalone overrides and explicit migration remain distinct
An explicit POWERSPEC_SAUCEPAN override SHALL be inspected for protocol compatibility and used without installing, updating, adopting or requiring managed ownership of it; explicit SDK clients SHALL keep their bypass. An unmanaged manager at the default path SHALL instead require the provider's explicit migration route, external or through init --force, or a standalone override. Migration consent SHALL NOT come from filename, version, cache records, ordinary init, upgrade or upgrade --force.

#### Scenario: Compatible explicit override
- **WHEN** a caller selects a standalone executable explicitly
- **THEN** source operations use it without provisioning or changing that executable

#### Scenario: Existing default raw manager
- **WHEN** init encounters the existing default raw manager without explicit migration
- **THEN** it preserves that file and reports the provider migration command and observed digest without executing displacement

#### Scenario: Provider migration completed
- **WHEN** the user explicitly completes Saucepan's verified migration and reruns Powerspec
- **THEN** Powerspec verifies and uses the owned launcher without deleting backups or replacing it through Zuu

#### Scenario: Upgrade does not authorize migration
- **WHEN** pspec upgrade or pspec upgrade --force encounters an unmanaged default manager
- **THEN** no migration consent is passed to the provider

#### Scenario: Forced initialization uses a ready installation
- **WHEN** init --force finds a ready compatible managed installation
- **THEN** it reuses the launcher without migration, release discovery, or self-update

#### Scenario: Forced initialization selects a standalone executable
- **WHEN** init --force uses an explicit standalone override or injected client
- **THEN** source refresh does not adopt, migrate, or replace that executable

## ADDED Requirements

### Requirement: Saucepan setup state stays provider-owned
The Saucepan provider SHALL own root initialization, application, claim and binding publication, shim ownership and recovery. Completed migrations SHALL be consumed through the verified managed launcher, with backups and migration receipts remaining provider-owned. SDK package version and binary protocol version SHALL remain independent, and Powerspec SHALL declare an immutable compatible SDK dependency without a legacy wire fallback.

#### Scenario: Incompatible protocol has no legacy fallback
- **WHEN** the manager does not support the pinned setup/SDK protocol
- **THEN** Powerspec reports incompatibility instead of falling back to a legacy wire protocol

### Requirement: Read-only and bundled-only operations never provision Saucepan
Read-only lookup, status and hook inspection SHALL inspect an existing executable and setup status within their remaining deadline, without provisioning, release discovery, setup, migration or filesystem initialization. Bundled-only operations SHALL NOT trigger installation. Without explicit migration authorization, a default unmanaged installation SHALL produce actionable diagnostics and keep its files; incomplete installations SHALL keep provider recovery requirements even with init --force.

#### Scenario: Incomplete installation under forced init
- **WHEN** init --force finds an incomplete provider installation
- **THEN** the provider's recovery requirements still apply and are not bypassed

### Requirement: Installer outcomes keep their operation identity
Complete setup SHALL be checked through the returned launcher and status contract. Recorded pending, failure or conflict outcomes and uncertain transport outcomes SHALL retain their operation identities and diagnostics, without automatic retry.

#### Scenario: Completed setup is confirmed before use
- **WHEN** the official installer reports completion
- **THEN** Powerspec confirms readiness through the returned launcher and status contract before creating a source client

#### Scenario: Recorded failure keeps its identity
- **WHEN** setup records a pending, failed or conflicting outcome
- **THEN** Powerspec reports that operation identity and its diagnostics without retrying automatically

### Requirement: Installer migration needs explicit forced consent
Source lifecycle authorization SHALL permit first setup but SHALL NOT imply consent to migrate an existing file. Init --force SHALL explicitly authorize provider-verified migration of a supported unmanaged default installation, using the observed file SHA256, the pinned installer and a stable operation ID.

#### Scenario: First setup needs no migration consent
- **WHEN** no installation exists and a source operation is authorized to materialize remote sources
- **THEN** official first setup proceeds without any migration consent

#### Scenario: Ordinary init does not migrate
- **WHEN** ordinary init finds a supported unmanaged default installation
- **THEN** it passes no migration consent and preserves the existing file


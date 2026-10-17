## ADDED Requirements

### Requirement: Default bootstrap initializes the store before executable publication
When provisioning the default `~/.saucepan/bin` manager into a missing or empty shared root, PowerSpec SHALL obtain and validate the manager outside the root, initialize the root through the public Saucepan SDK, and only then publish the manager. Successful release-check caching SHALL survive publication at the final destination. Existing store contents SHALL remain under Saucepan's validation authority. Explicit executable destinations outside the default location and injected clients SHALL retain their existing behavior. Read-only operations SHALL NOT bootstrap or recover stores.

#### Scenario: First installation in an empty home
- **WHEN** an authorized source operation needs the default manager and no shared store exists
- **THEN** initialization runs with an empty root and an external executable before final publication, and source acquisition can proceed

#### Scenario: Repeated installation
- **WHEN** the store and a freshly checked compatible manager already exist
- **THEN** the operation reuses them without initialization or release discovery

#### Scenario: Initialization failure
- **WHEN** the manager cannot initialize the new store
- **THEN** PowerSpec reports the initialization failure and does not publish a binary into that root or claim successful setup

### Requirement: Binary-only bootstrap recovery preserves installer assets
PowerSpec SHALL recover only a plain default root containing a plain `bin` directory with regular installer files named for the manager and its release-check record, and no other content. A present manager SHALL pass compatibility and command checks before recovery. Recovery SHALL preserve the original directory in an external backup before invoking Saucepan initialization. Unknown files, links, junctions, and existing store data SHALL NOT be moved or deleted by this recovery. Concurrent PowerSpec bootstrap attempts SHALL serialize or fail clearly before conflicting mutations. Recovery diagnostics SHALL identify preserved backup locations on failure; backups SHALL survive failure and success. Interrupted initialization SHALL remain subject to Saucepan's own resume guards.

#### Scenario: Previous installer left only a manager and check record
- **WHEN** initialization encounters the recognized binary-only root
- **THEN** its original files are preserved outside the root and initialization precedes publishing the validated manager

#### Scenario: Unknown files or linked paths
- **WHEN** the uninitialized default root contains other data or linked recovery paths
- **THEN** PowerSpec refuses automatic recovery and leaves those paths untouched

#### Scenario: Failed recovery can be retried
- **WHEN** initialization or publication fails after preserving the original bin directory
- **THEN** the originals remain in the reported backup, and a later attempt handles an empty or Saucepan-recognized interrupted root without deleting data

#### Scenario: Another bootstrap is active
- **WHEN** a second PowerSpec bootstrap targets the same default location
- **THEN** it does not move or publish over the first operation's files

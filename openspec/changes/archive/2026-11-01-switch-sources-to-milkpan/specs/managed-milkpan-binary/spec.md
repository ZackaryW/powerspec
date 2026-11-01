# Spec Delta

## Purpose

Provide Powerspec's source store with a pinned, verified milkpan that manages itself in Powerspec's own home, updating on the next run, with a standalone override and no provisioning for read-only work.

## ADDED Requirements

### Requirement: Powerspec pins a verified milkpan release
Powerspec SHALL pin one milkpan release tag and the SHA-256 of each supported platform asset. Bootstrapping SHALL download only the current platform's asset from that tag on GitHub, reject it unless its digest matches the pin (within a size limit), and extract it outside the milkpan home before use. Unsupported platforms SHALL fail with a message naming the supported ones.

#### Scenario: Tampered download
- **WHEN** the downloaded asset's SHA-256 differs from the pinned digest
- **THEN** bootstrap fails before extracting or running anything

#### Scenario: Unsupported platform
- **WHEN** Powerspec runs on a platform without a pinned asset
- **THEN** source preparation fails naming the supported platforms

### Requirement: Powerspec keeps milkpan in its own home
Powerspec SHALL keep its milkpan home at `~/.powerspec/milkpan`, overridable by `POWERSPEC_MILKPAN_HOME`. After the first verified bootstrap, it SHALL acquire milkpan's own pinned release asset in scope `powerspec-manager` with that binary, confirm the lease digest equals the pinned digest, and link it as `milkpan`. Later invocations SHALL run the linked executable.

#### Scenario: First preparation
- **WHEN** no milkpan home exists and a source must be prepared
- **THEN** Powerspec bootstraps the pinned release, links it as `milkpan` and runs source operations through the link

#### Scenario: Digest mismatch after acquiring
- **WHEN** the acquired release lease's digest differs from the pinned digest
- **THEN** preparation fails and leaves any existing link unchanged

### Requirement: Milkpan updates on the next run
When Powerspec pins a newer milkpan release than the linked one, the next preparation or upgrade SHALL acquire and link the newly pinned asset. The switch SHALL take effect on the following invocation, while processes already running keep their version.

#### Scenario: Powerspec upgrade pins a newer milkpan
- **WHEN** the linked milkpan's lease digest differs from the newly pinned digest
- **THEN** preparation acquires the newly pinned asset and repoints the link, and the next invocation runs the new version

### Requirement: Compatibility is checked before use
Before running source operations, Powerspec SHALL require the selected milkpan to report protocol version 1 through `protocol` and a version in its supported release line. An incompatible executable SHALL fail with guidance, without modifying it.

#### Scenario: Old executable
- **WHEN** the selected milkpan does not support protocol 1 or reports an unsupported version
- **THEN** source preparation fails with update guidance and changes nothing

### Requirement: A standalone override bypasses management
When `POWERSPEC_MILKPAN` names an executable, Powerspec SHALL use it as-is after the compatibility check, SHALL NOT bootstrap, link, update or adopt it, and SHALL label it standalone in diagnostics.

#### Scenario: Developer build
- **WHEN** `POWERSPEC_MILKPAN` points at a locally built milkpan
- **THEN** sources are prepared through it and no managed link is created or changed

### Requirement: Powerspec owns its milkpan policy
Powerspec SHALL write the policy file in its milkpan home. It SHALL contain rules allowing the manager scope to manage milkpan's own release, and allowing each consumer's scopes to acquire, reacquire, read and release GitHub and local sources. Each consumer rule SHALL carry a lease obligation that keeps selected leases from expiring and sets a one-day refresh. A rule for a new consumer SHALL be added under a lock before its first acquisition.

#### Scenario: New consumer
- **WHEN** a consumer prepares its first source
- **THEN** its scope rules exist in the policy file before milkpan is asked to acquire

### Requirement: Read-only and bundled-only operations never provision milkpan
Lookup, status, hook resolution, doctor and bundled-only installation SHALL NOT download, bootstrap, link or update milkpan, and SHALL report missing or incompatible milkpan as unavailable metadata where a source is needed.

#### Scenario: Status on a fresh machine
- **WHEN** status runs before any source preparation
- **THEN** it reports sources as not yet prepared without downloading milkpan

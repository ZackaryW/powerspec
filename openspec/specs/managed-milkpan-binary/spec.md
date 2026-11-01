# managed-milkpan-binary Specification

## Purpose

Provide Powerspec's source store with a pinned, verified milkpan that manages itself in Powerspec's own home, updating on the next run, with a standalone override and no provisioning for read-only work.

## Requirements

### Requirement: Powerspec pins a verified milkpan release
Powerspec SHALL pin one milkpan release tag and the SHA-256 of each supported platform asset. Bootstrapping SHALL download only the current platform's asset from that tag on GitHub, reject it unless its digest matches the pin (within a size limit), and extract it outside the milkpan home before use. Unsupported platforms SHALL fail with a message naming the supported ones.

#### Scenario: Tampered download
- **WHEN** the downloaded asset's SHA-256 differs from the pinned digest
- **THEN** bootstrap fails before extracting or running anything

#### Scenario: Unsupported platform
- **WHEN** Powerspec runs on a platform without a pinned asset
- **THEN** source preparation fails naming the supported platforms

### Requirement: Milkpan updates on the next run
When the shared milkpan link is missing, or links a milkpan outside the release lines Powerspec supports, the next preparation or upgrade SHALL acquire and link Powerspec's pinned release. The switch SHALL take effect on the following invocation, while processes already running keep their version. A linked milkpan in a supported release line SHALL NOT be replaced, even when it differs from the pin.

#### Scenario: Powerspec upgrade pins a newer milkpan
- **WHEN** a new Powerspec supports only a newer release line than the linked milkpan's
- **THEN** preparation acquires the newly pinned asset and repoints the link, and the next invocation runs the new version

#### Scenario: Newer compatible milkpan installed by the user
- **WHEN** the shared link holds a newer milkpan in a supported release line than Powerspec's pin
- **THEN** Powerspec uses it and leaves the link unchanged

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

### Requirement: Read-only and bundled-only operations never provision milkpan
Lookup, status, hook resolution, doctor and bundled-only installation SHALL NOT download, bootstrap, link or update milkpan, and SHALL report missing or incompatible milkpan as unavailable metadata where a source is needed.

#### Scenario: Status on a fresh machine
- **WHEN** status runs before any source preparation
- **THEN** it reports sources as not yet prepared without downloading milkpan

### Requirement: Powerspec uses the shared milkpan bucket
Powerspec SHALL resolve its bucket exactly as milkpan does (`MILKPAN_HOME`, then `.milkpan` in the user's home directory), so plain milkpan use and Powerspec share stored content. When no usable link exists, the first verified bootstrap SHALL acquire milkpan's pinned release asset in scope `powerspec/manager`, confirm the lease digest equals the pinned digest, and link it as `milkpan`. Later invocations SHALL run the linked executable.

#### Scenario: First preparation
- **WHEN** no shared milkpan link exists and a source must be prepared
- **THEN** Powerspec bootstraps the pinned release into `~/.milkpan`, links it as `milkpan` and runs source operations through the link

#### Scenario: Digest mismatch after acquiring
- **WHEN** the acquired release lease's digest differs from the pinned digest
- **THEN** preparation fails and leaves any existing link unchanged

#### Scenario: Content shared with plain milkpan
- **WHEN** a user already acquired a GitHub commit with plain `milkpan` and a Powerspec recipe resolves to the same commit
- **THEN** Powerspec's selection reuses the stored content without downloading it again

### Requirement: Powerspec manages a marked block of the shared policy
Powerspec SHALL keep its rules in one marked block of the shared `milkpan.toml`, rewriting only that block under a lock and preserving everything outside it byte for byte. The block SHALL allow `powerspec/manager` to manage milkpan's own release, and each consumer's `powerspec/consumer-<hash>` and candidate scopes to use GitHub and local sources with their lease obligations. When no rule outside the block covers scope `default`, the block SHALL also allow every lease operation in `default`.

#### Scenario: User rules survive
- **WHEN** the shared policy file has user rules for scope `ci` and Powerspec adds a consumer
- **THEN** the `ci` rules are unchanged and the consumer's rules appear inside the block

#### Scenario: Default scope keeps working
- **WHEN** Powerspec writes its block into a bucket whose policy had no rules
- **THEN** plain `milkpan acquire` in scope `default` is still allowed

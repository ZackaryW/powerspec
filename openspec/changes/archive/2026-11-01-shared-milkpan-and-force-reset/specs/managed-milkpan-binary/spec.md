# Spec Delta

## MODIFIED Requirements

### Requirement: Milkpan updates on the next run
When the shared milkpan link is missing, or links a milkpan outside the release lines Powerspec supports, the next preparation or upgrade SHALL acquire and link Powerspec's pinned release. The switch SHALL take effect on the following invocation, while processes already running keep their version. A linked milkpan in a supported release line SHALL NOT be replaced, even when it differs from the pin.

#### Scenario: Powerspec upgrade pins a newer milkpan
- **WHEN** a new Powerspec supports only a newer release line than the linked milkpan's
- **THEN** preparation acquires the newly pinned asset and repoints the link, and the next invocation runs the new version

#### Scenario: Newer compatible milkpan installed by the user
- **WHEN** the shared link holds a newer milkpan in a supported release line than Powerspec's pin
- **THEN** Powerspec uses it and leaves the link unchanged

## REMOVED Requirements

### Requirement: Powerspec keeps milkpan in its own home
**Reason**: Powerspec uses the shared `~/.milkpan` bucket instead of a private one.
**Migration**: See "Powerspec uses the shared milkpan bucket". Consumers selected through `~/.powerspec/milkpan` re-run `pspec init`; `POWERSPEC_MILKPAN_HOME` is replaced by milkpan's `MILKPAN_HOME`.

### Requirement: Powerspec owns its milkpan policy
**Reason**: A shared bucket's policy file also holds the user's rules.
**Migration**: See "Powerspec manages a marked block of the shared policy".

## ADDED Requirements

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

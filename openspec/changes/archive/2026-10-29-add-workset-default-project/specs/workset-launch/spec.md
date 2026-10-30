# Spec Delta

## ADDED Requirements

### Requirement: Launch carries the default to the output workset
When the source workset has a current default, a successful launch SHALL record the same label as the output workset's default, with the launched worktree path and the output members' paths. If the output already has the same default it SHALL be reused; a different existing default SHALL be kept and reported, not overwritten. A stale or absent source default SHALL record nothing.

#### Scenario: Default follows the launch
- **WHEN** `poc-ab` has default `poc-ab-central` and `pspec workset launch poc-ab --branch feature-x` succeeds
- **THEN** `poc-ab-feature-x` has default `poc-ab-central` pointing at that member's new worktree

#### Scenario: Output already has a different default
- **WHEN** the output workset already has a different default
- **THEN** launch keeps it and reports that the source default was not applied

#### Scenario: Incomplete launch
- **WHEN** launch does not publish the output workset
- **THEN** no default is recorded for it

### Requirement: Append keeps the default snapshot current
After `pspec workset add` appends a member to a workset that has a current default, Powerspec SHALL refresh that default's member snapshot to the verified new membership without changing the default label. A failed append SHALL leave the stored default unchanged.

#### Scenario: Append to a workset with a default
- **WHEN** a repository is appended to `poc-ab` whose default is current
- **THEN** the default stays `poc-ab-central` and its snapshot includes the new member

#### Scenario: Append fails
- **WHEN** the append fails and the original workset is restored
- **THEN** the stored default and snapshot are unchanged

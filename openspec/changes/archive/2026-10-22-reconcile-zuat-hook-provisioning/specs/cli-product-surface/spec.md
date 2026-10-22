# Spec Delta

## MODIFIED Requirements

### Requirement: Upgrade refreshes before committing removals

`pspec upgrade --agent <agent>` SHALL refresh selected Saucepan sources, compose the refreshed effective bundle, reconcile skills and hooks, and remove obsolete managed installations only after every required refresh and reconciliation step succeeds. The upgrade command SHALL reuse a compatible Saucepan installation and SHALL NOT implicitly self-update the shared manager; incompatibility SHALL report explicit provider update guidance before source refresh. `sync` SHALL continue to preserve the currently materialized revisions rather than refreshing them.

Upgrade SHALL accept `--repair-hooks` as separate explicit authorization to repair a valid stale hook ownership receipt when the uniquely identified native hooks already match the desired source. The existing `--force` option SHALL remain limited to selected skill replacement. Hook repair SHALL NOT authorize arbitrary hook replacement or bypass incomplete inspection. Failed reconciliation SHALL retain provider diagnostics and any recovery operation identifier; successful repair SHALL display its operation identifier. Initialization SHALL NOT implicitly authorize receipt repair.

#### Scenario: Successful upgrade
- **WHEN** all selected sources refresh and the resulting installation succeeds
- **THEN** Powerspec commits additions, updates, and obsolete managed removals for the agent

#### Scenario: Upgrade fails before completion
- **WHEN** any required refresh or reconciliation step fails
- **THEN** Powerspec reports failure without committing obsolete-source removals

#### Scenario: Skill force does not repair hooks
- **WHEN** upgrade uses --force without --repair-hooks and finds a stale hook receipt
- **THEN** it reports hook reconciliation failure and preserves obsolete skills

#### Scenario: Authorized hook repair
- **WHEN** upgrade uses --repair-hooks and a valid stale receipt identifies hooks already matching the desired source
- **THEN** ownership is repaired through ZuAT, its recovery identifier is displayed, and upgrade continues after successful reconciliation

#### Scenario: Ambiguity despite repair option
- **WHEN** upgrade uses --repair-hooks but hook identity is unresolved
- **THEN** upgrade exits nonzero without claiming success or removing obsolete skills

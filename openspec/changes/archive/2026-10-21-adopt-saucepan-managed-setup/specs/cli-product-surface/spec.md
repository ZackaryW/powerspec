# Spec Delta

## MODIFIED Requirements

### Requirement: First-use source preparation preserves existing stores
Source preparation SHALL delegate missing-store initialization and managed launcher publication to Saucepan through its official setup contract. Powerspec SHALL not publish the raw manager at the default launcher path or move existing installer leftovers. An unmanaged occupant SHALL require explicit Saucepan migration or an explicit standalone override; ordinary init/upgrade SHALL not supply migration consent. It SHALL NOT replace credentials, delete existing store data, bypass guards, or substitute test keys. Credential-service or damaged-store failures SHALL remain errors without a success claim. A failed or uncertain provider setup SHALL direct the user to inspect and explicitly resume the original provider operation where applicable, then rerun init with the same source options; upgrade SHALL NOT silently replace missing-only initialization.

#### Scenario: Fresh native store
- **WHEN** a store is absent and Saucepan permits initialization
- **THEN** Saucepan setup completes the managed installation before PowerSpec registers its resource-consumer application and continues acquisition

#### Scenario: Existing store cannot be initialized
- **WHEN** Saucepan rejects initialization because existing data or credential problems prevent it
- **THEN** PowerSpec reports failure without registering or acquiring sources or replacing store contents

#### Scenario: Failed binary-only setup
- **WHEN** the former installer left only recognized installer files under the default root
- **THEN** rerunning init preserves those files in place and reports the provider-supported manual preservation or separate-root prerequisite without moving them

#### Scenario: Canonical GitHub source identity
- **WHEN** Saucepan returns the same HTTPS GitHub repository with canonical lowercase owner/repository spelling and the normal .git suffix
- **THEN** source preparation accepts that identity while preserving host, transport, query, and reference distinctions; other hosts retain case-sensitive repository paths

### Requirement: Doctor distinguishes executable checks from source readiness
Doctor SHALL identify its successful Saucepan observation as an executable compatibility check, without implying that selected materializations have been initialized. For the default managed route it SHALL separately inspect Saucepan setup status when supported, distinguishing ready, unmanaged, absent, pending and conflict states; version alone SHALL not establish managed ownership. An explicit executable override SHALL be labelled standalone and inspected without adoption or update. Human and JSON results SHALL preserve the named check and indicate this limitation without mutating resources. User instructions SHALL distinguish explicit provider setup recovery from subsequent source initialization with init before upgrade.

#### Scenario: Compatible binary but no selected source
- **WHEN** doctor observes a compatible Saucepan executable
- **THEN** its detail identifies executable compatibility, reports managed installation status separately when applicable, and states that selected-source readiness was not checked

#### Scenario: Compatible raw binary at the default path
- **WHEN** a version-compatible raw manager occupies the default managed launcher path
- **THEN** doctor distinguishes executable compatibility from missing managed ownership and reports explicit migration guidance without modifying the file

#### Scenario: Explicit standalone override
- **WHEN** the user selects an external manager through POWERSPEC_SAUCEPAN
- **THEN** doctor labels that selection standalone without requiring managed ownership or changing the binary

### Requirement: Upgrade refreshes before committing removals

`pspec upgrade --agent <agent>` SHALL refresh selected Saucepan sources, compose the refreshed effective bundle, reconcile skills and hooks, and remove obsolete managed installations only after every required refresh and reconciliation step succeeds. The upgrade command SHALL reuse a compatible Saucepan installation and SHALL NOT implicitly self-update the shared manager; incompatibility SHALL report explicit provider update guidance before source refresh. `sync` SHALL continue to preserve the currently materialized revisions rather than refreshing them.

#### Scenario: Successful upgrade
- **WHEN** all selected sources refresh and the resulting installation succeeds
- **THEN** Powerspec commits additions, updates, and obsolete managed removals for the agent

#### Scenario: Upgrade fails before completion
- **WHEN** any required refresh or reconciliation step fails
- **THEN** Powerspec reports failure without committing obsolete-source removals

## MODIFIED Requirements

### Requirement: First-use source preparation preserves existing stores
Source preparation SHALL delegate missing-store initialization to Saucepan. Default managed-binary bootstrap SHALL initialize before publication and MAY preserve narrowly recognized binary-only installer leftovers outside the root before retrying. It SHALL NOT replace credentials, delete existing store data, bypass guards, or substitute test keys. Credential-service or damaged-store failures SHALL remain errors without a success claim. A failed setup SHALL direct the user to rerun init with the same options; upgrade SHALL NOT silently replace missing-only initialization.

#### Scenario: Fresh native store
- **WHEN** a store is absent and Saucepan permits initialization
- **THEN** PowerSpec initializes, registers its application, and continues acquisition

#### Scenario: Existing store cannot be initialized
- **WHEN** Saucepan rejects initialization because existing data or credential problems prevent it
- **THEN** PowerSpec reports failure without registering or acquiring sources or replacing store contents

#### Scenario: Failed binary-only setup
- **WHEN** the former installer left only recognized installer files under the default root
- **THEN** rerunning init preserves those files outside the root and proceeds through store initialization before acquisition

#### Scenario: Canonical GitHub source identity
- **WHEN** Saucepan returns the same HTTPS GitHub repository with canonical lowercase owner/repository spelling and the normal .git suffix
- **THEN** source preparation accepts that identity while preserving host, transport, query, and reference distinctions; other hosts retain case-sensitive repository paths

## ADDED Requirements

### Requirement: Doctor distinguishes executable checks from source readiness
Doctor SHALL identify its successful Saucepan observation as an executable compatibility check, without implying that a shared store or selected materializations have been initialized. Human and JSON results SHALL preserve the named check and indicate this limitation without mutating resources. User instructions SHALL explain that incomplete setup is resumed with init before upgrade.

#### Scenario: Compatible binary but no selected source
- **WHEN** doctor observes a compatible Saucepan executable
- **THEN** its detail identifies executable compatibility and that store/source readiness was not checked

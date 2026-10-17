## ADDED Requirements

### Requirement: Doctor reports evidence for guidance delivery stages
`pspec doctor --agent codex|claude` SHALL add read-only diagnostics to the existing prerequisite checks. It SHALL distinguish effective zmem profile selection, current persistent rule publication, matching startup/compaction registrations, observable native disabled settings, resolver generation for both events, and host receipt/adherence. Resolver generation SHALL use the installed hook command with finite timeouts and validate its native envelope. Source warnings SHALL remain visible. Host receipt, effective enablement/trust beyond inspected settings, and adherence SHALL be explicitly unverified unless directly established; successful generation alone SHALL NOT establish them. Unknown verification SHALL be reported as warning, observed failures SHALL cause nonzero exit, and JSON SHALL remain a single structured result. Unsupported agents SHALL fail before probes. Omitting --agent SHALL retain basic checks and indicate that delivery checks were not requested. Doctor SHALL NOT install, enable, trust, repair or acquire resources.

#### Scenario: Hook registered but disabled
- **WHEN** native settings explicitly disable a matching PowerSpec callback
- **THEN** doctor reports the observed disabled setting and exits unsuccessfully without changing it

#### Scenario: Guidance generated without host observation
- **WHEN** both resolver commands emit valid context
- **THEN** generation passes while host receipt and adherence remain unverified

#### Scenario: Stale or missing published context
- **WHEN** the zmem profile is selected but the current standing rule is absent from config.yaml
- **THEN** doctor reports the publication gap rather than claiming complete delivery

#### Scenario: Missing sources
- **WHEN** resolver output contains metadata warnings but still carries the required rule
- **THEN** doctor preserves those warnings and does not repair sources

#### Scenario: Excluded policy
- **WHEN** zmem is excluded
- **THEN** doctor reports intentional nonselection without treating its absent guidance as a failure

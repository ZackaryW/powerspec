# Spec Delta

## MODIFIED Requirements

### Requirement: Provision generic user-level hook dispatchers through ZuAT

Powerspec provisioning SHALL install generic `pspec resolve hook` command registrations on the explicitly selected agent's supported user-level hook surfaces through ZuAT. Every generated advisory command handler SHALL carry an explicit timeout of no more than five seconds and a concise status message. Registrations SHALL carry the native context needed to select guidance at invocation rather than embedding one consumer's profile or trait body, and SHALL NOT return a blocking host decision. Unsupported surfaces SHALL be reported without guessing native events or falling back to repository-local installation.

Repeated provisioning SHALL preserve unrelated hooks/settings, reuse matching registrations, and report modified or unmanaged conflicts without silently overwriting them. Reconciliation SHALL replace safely owned earlier Powerspec registrations, including legacy command aliases and broader resume matchers, without retaining duplicate callbacks. It SHALL NOT remove or rewrite callbacks owned by another tool. Guidance selection SHALL remain a trait-level concern.

Provisioning SHALL require complete inspection before any mutation. Current owned source-matching hooks SHALL be reused; safely outdated owned hooks SHALL be updated without force; exact unowned source-matching groups SHALL be adopted without rewriting native bytes; only verified absent groups SHALL be installed. Indeterminate, unsupported, ambiguous, or conflicting groups SHALL fail with diagnostics without an installation fallback.

Explicit hook repair SHALL permit only a valid owned receipt conflict whose uniquely identified native group already matches the desired source. Repair SHALL use ZuAT's targeted recoverable update, preserve native bytes and modification time, and retain the recovery operation identifier. Authorization SHALL NOT permit replacement of edited content, positional overwrites, duplicate candidates, invalid receipts, or cross-provider targets.

#### Scenario: Repeated dispatcher provisioning
- **WHEN** the selected agent already has matching bounded Powerspec registrations alongside unrelated hooks
- **THEN** provisioning preserves unrelated entries and does not duplicate Powerspec callbacks

#### Scenario: Safely owned earlier callback shape
- **WHEN** ZuAT identifies an unmodified Powerspec-owned registration using a legacy command or resume matcher
- **THEN** provisioning replaces it with the current bounded registration and leaves unrelated providers untouched

#### Scenario: Consumer changes its selected hook traits
- **WHEN** a consumer changes profile selection after user-level hooks have been installed
- **THEN** subsequent matching lifecycle callbacks resolve that consumer's new effective hook traits without rewriting shared registrations

#### Scenario: Exact unowned registration
- **WHEN** complete inspection identifies a unique unowned group exactly matching the desired hooks
- **THEN** provisioning adopts ownership without modifying native bytes or duplicating callbacks

#### Scenario: Unresolved group identity
- **WHEN** inspection is incomplete, ambiguous, or indeterminate, including unowned legacy hooks that cannot be uniquely identified
- **THEN** provisioning reports failure and preserves native settings without attempting installation

#### Scenario: Receipt repair is explicit
- **WHEN** the installed group matches the desired source but its valid owned receipt is stale
- **THEN** ordinary provisioning fails with explicit repair guidance
- **AND** authorized repair reconciles ownership without changing native bytes or modification time and reports a recovery operation identifier

#### Scenario: Repair does not authorize unrelated replacement
- **WHEN** hook repair is authorized but the installed content differs from the desired source or selection is ambiguous
- **THEN** provisioning fails without rewriting settings or replacing an occupant by its array position

#### Scenario: Native hooks change after consumer inspection
- **WHEN** another writer restores the older owned hooks after Powerspec inspects a source-matching receipt conflict but before repair runs
- **THEN** the provider rechecks receipt-only eligibility inside the update operation and rejects repair without replacing the concurrent content

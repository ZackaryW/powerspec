# Spec Delta

## REMOVED Requirements

### Requirement: Default source clients ensure a compatible Saucepan executable
**Reason**: Powerspec's source store uses milkpan instead of Saucepan.
**Migration**: See `managed-milkpan-binary`: "Powerspec pins a verified milkpan release" and "Compatibility is checked before use".

### Requirement: Managed checks preserve usable tools and avoid needless discovery
**Reason**: The Saucepan launcher and its discovery are no longer used.
**Migration**: See `managed-milkpan-binary`: "Milkpan manages itself in Powerspec's home".

### Requirement: Explicit clients bypass managed provisioning
**Reason**: The Saucepan SDK client is removed.
**Migration**: Tests and callers inject a milkpan-backed source store or set `POWERSPEC_MILKPAN`; see "A standalone override bypasses management".

### Requirement: Official installer invocation preserves authorization and receipts
**Reason**: Saucepan's installer scripts and receipts are not used; milkpan is bootstrapped from a verified release asset.
**Migration**: See "Powerspec pins a verified milkpan release".

### Requirement: Standalone overrides and explicit migration remain distinct
**Reason**: There is no Saucepan store to migrate into; milkpan lives in Powerspec's own home.
**Migration**: `POWERSPEC_SAUCEPAN` is replaced by `POWERSPEC_MILKPAN`; see "A standalone override bypasses management".

### Requirement: Saucepan setup state stays provider-owned
**Reason**: Saucepan setup state is no longer read or written.
**Migration**: The old store is left untouched and ignored; consumers re-run `pspec init`.

### Requirement: Read-only and bundled-only operations never provision Saucepan
**Reason**: Superseded by the milkpan equivalent.
**Migration**: See `managed-milkpan-binary`: "Read-only and bundled-only operations never provision milkpan".

### Requirement: Installer outcomes keep their operation identity
**Reason**: Installer operations and receipts are removed.
**Migration**: Milkpan operations are idempotent per spec and scope, so a retried preparation reuses the same lease.

### Requirement: Installer migration needs explicit forced consent
**Reason**: Unmanaged Saucepan migration is removed.
**Migration**: None needed; milkpan uses Powerspec's own home and never adopts another installation.

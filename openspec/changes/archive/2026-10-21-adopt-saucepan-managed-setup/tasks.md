# Tasks

## 1. Provider contract adapter and inspection

- [x] 1.1 Add a feature-owned immutable provider descriptor and setup/status response validation against the completed add-managed-setup contract, with explicit local fixture selection for development; verify supported schema/platform/version checks and reject malformed or placeholder production descriptors.
- [x] 1.2 Replace default raw-file/version-only readiness with bounded version and managed-status inspection using existing utilities; verify ready/unmanaged/pending/conflict/corrupt states, root/launcher mismatches and shared deadline exhaustion through focused adapter tests developed with the repository's TDD workflow.
- [x] 1.3 Preserve explicit standalone overrides and injected-client bypass while removing Zuu manager-refresh/cache decisions; verify no discovery, replacement, cache deletion or setup for compatible reuse, explicit clients and bundled-only operations, and document these ownership modes in the same checkpoint.

## 2. Authorized official first setup

- [x] 2.1 Replace raw publication and binary-leftover relocation with checksum-verified external installer staging and literal bounded invocation using a stable operation ID; verify first-use setup with the local provider fixture, missing prerequisites and checksum failures without direct writes to provider launcher/metadata paths.
- [x] 2.2 Preserve setup JSON and exit-2 receipts through a feature-owned subprocess adapter, forward progress to stderr and reinspect complete results before client creation; verify pending/failure/conflict, malformed output and response-loss uncertainty retain root/operation evidence without automatic mutation retry.
- [x] 2.3 Report explicit provider migration/recovery guidance for existing unmanaged managers and incomplete roots without supplying migration consent; verify actual init entrypoint behavior preserves raw bytes, sidecars, binary-only leftovers, credentials and existing consumer state.
- [x] 2.4 Document first setup, provider-operation recovery before rerunning init, standalone selection and old-consumer coexistence; verify documented commands and diagnostics with isolated homes and ensure read-only/hook paths cannot enter installer code.

## 3. Doctor and resource-upgrade behavior

- [x] 3.1 Separate executable compatibility, managed installation state and selected-source readiness in human/JSON doctor output; verify actual CLI results for absent, old raw, ready, pending and explicit standalone cases without resource or store mutation.
- [x] 3.2 Keep pspec upgrade limited to selected resource refresh and agent reconciliation, reporting incompatibility before source effects; verify a ready manager is reused without self-update/discovery and failed refresh still preserves obsolete installations until reconciliation succeeds.
- [x] 3.3 Update CLI guidance and regressions for init, sync, doctor, upgrade and hook/skill protocols; verify output/exit/deadline contracts and unchanged source generation pinning/retention, and reconcile overlap with add-pspec-skill-routing without absorbing its tasks.

## 4. Released-artifact and installed-package acceptance

- [x] 4.1 Once actual setup-capable provider release evidence exists, pin its immutable tag, installer checksum and compatible SDK revision and update the lockfile; verify the SDK and binary versions independently and reject an unpublished/default placeholder. Keep this task pending while only local build fixtures exist; publishing the provider release is a separate action.
- [x] 4.2 Build/install Powerspec outside the checkout and exercise its actual entrypoint against the released provider artifacts in isolated roots; verify fresh setup, managed reuse and consumption of an explicitly migrated store without Rust or a Saucepan checkout, and retain hashes and operation evidence.
- [x] 4.3 Run the required Python checks and affected source/bootstrap/CLI/protocol suites, then openspec validate adopt-saucepan-managed-setup --strict --no-interactive; verify no production-home mutation and report any remaining provider release gate instead of marking acceptance complete.

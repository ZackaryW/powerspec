# Tasks

## 1. Shared application mechanics

- [x] 1.1 Extract a domain-neutral atomic byte replacement helper and verify unchanged, successful replacement, failure preservation, and staging cleanup with isolated filesystem tests
- [x] 1.2 Add bounded executable inspection and structured result presentation primitives, and verify success, missing command, nonzero exit, timeout, human output, and JSON output with focused tests
- [x] 1.3 Add the shared consumer workspace loader with explicit lookup and acquisition modes, and verify local resources, exclusions, and read-only source lookup without acquisition

## 2. Setup and installation lifecycle

- [x] 2.1 Refactor initialization into a setup-only application use case that accepts an optional profile and global-only selection, and verify repeated initialization preserves existing consumer bytes and performs no provisioning
- [x] 2.2 Implement `install --agent` using Saucepan acquisition, effective bundle composition, ZuAT provisioning, and hook reconciliation, and verify acquisition, declared scopes, partial failures, and convergent repeat installation
- [x] 2.3 Update lifecycle help and documentation for the explicit `init` then `install` flow, and verify documented commands match installed CLI help

## 3. Organized command surface and compatibility

- [x] 3.1 Register the human control-plane commands and `state`, `resolve`, and `config` groups, while retaining hidden `skill`, `hook`, and `flush` aliases; verify both console entrypoints, group help, syntax errors, and alias equivalence
- [x] 3.2 Move existing skill, hook, and temporary-state adapters behind the grouped commands without changing their protocol payloads, and verify Markdown, JSON, stdin payload, change scope, and exit-code compatibility

## 4. Inspection and configuration

- [x] 4.1 Implement mutation-free `status` with human and JSON output for the effective profiles, resources, source availability, and pending installation facts; verify it never acquires or changes resources
- [x] 4.2 Implement mutation-free `doctor` prerequisite checks and verify named pass/fail results, supported OpenSpec version detection, missing tools, nonzero exit, and JSON output
- [x] 4.3 Implement `config show`, `config profile`, `config edit`, and `state show`; verify round-trip-safe profile changes, selector clearing, preserved variables and comments, editor errors, scoped temporary values, and JSON output

## 5. Synchronization and upgrade consistency

- [x] 5.1 Make sync use the shared local-aware workspace and complete validation before atomic publication; verify local overrides, unavailable remote preservation, user YAML preservation, and unchanged repeats
- [x] 5.2 Reuse installation reconciliation from upgrade while preserving refresh-first and remove-only-after-total-success behavior; verify successful refresh, failed refresh, hook outcome, and obsolete removal boundaries

## 6. Integration verification

- [x] 6.1 Run strict validation for the change, execute the complete pytest suite through `uv run pytest`, build wheel and sdist artifacts, and inspect installed `pspec` and `powerspec` help plus representative lifecycle commands

# Proposal

## Why

The TDD and BDD skills require observable outcomes but do not explicitly reject tests that only match implementation text or pin incidental prose. Such checks can pass while behavior is broken, creating maintenance work and overstating verification.

## What Changes

- Require each test to establish an accepted behavior, regression, or externally meaningful contract through an appropriate production boundary.
- Prohibit string, regex, snapshot, and source-shape checks used only to mirror implementation or manufacture test coverage. Retain text assertions when text is the actual contract, with structured assertions preferred for structured data.
- Strengthen TDD and BDD guidance with concrete examples and a check that a plausible violation of the claimed behavior would make the test fail.
- Add concise verification-quality reminders to existing Python CLI task-planning and apply governance, without copying entire skill procedures or activating BDD.
- Review the directly affected skill-resolution and guidance-delivery tests, preserving useful coverage while removing incidental wording dependencies. Do not manufacture tests merely to verify that the new rule contains particular words.

## Capabilities

### New Capabilities

- `behavioral-test-evidence`: Quality and evidence boundaries for TDD, BDD, and selected planning/apply guidance, including legitimate text contracts and proportional verification.

### Modified Capabilities

None. Existing profile selection, dynamic resolution, and publication mechanics remain unchanged.

## Impact

The implementation affects `.pspec/skills/pspec-tdd`, `.pspec/skills/pspec-bdd`, the existing Python CLI context, and directly relevant tests. No new runtime dependency, test framework, enforcement engine, automatic BDD selection, or repository-wide test rewrite is introduced. Generated governance is published through the existing sync path during implementation. This capture creates planning artifacts only.

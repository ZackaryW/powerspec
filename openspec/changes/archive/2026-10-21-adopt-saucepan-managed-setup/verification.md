# Verification

Implemented `adopt-saucepan-managed-setup`; all 13 scoped tasks are complete. Specs were synced and the change archived on 2026-10-21 for the focused implementation commit. `add-pspec-skill-routing` remains separate and untouched. No Powerspec release or real-home Saucepan migration was performed.

## Provider and package evidence

- Published provider: [Saucepan v0.11.0](https://github.com/ZackaryW/saucepan/releases/tag/v0.11.0), commit `324282bac14fd0e0032a07e0fbed85ee95447dbb`.
- SDK independently reports `0.3.0`; released executable reports `saucepan 0.11.0+v0.11.0`.
- `install.ps1` SHA256: `40bfe6d67766b1f0f31cd87847ed982dcf910b789dcb930cd66b119047f3e471`.
- `install.sh` SHA256: `2930797ce66a7b43f5670643451a461d711dd2effa1db389a39fc8178aacc696`.
- Windows x64 ZIP SHA256: `2e4ca74531dbd5b8374a2947ab3287b2353af192f860e6cdbe1fddd4ebe927c2`.
- Wheel built with `uv build --wheel`, installed in an independent temporary virtual environment, and imported from that environment's site-packages. Actual `pspec.exe` ran from temporary consumer repositories. The installer used published GitHub artifacts with no provider checkout or Rust build/runtime in the acceptance flow.
- Both fresh setup and separately consented provider migration passed init, repeat init, doctor JSON and resource upgrade. Launcher hashes stayed unchanged through reuse/upgrade, source generations changed on upgrade, and the migration backup matched the original raw manager hash. See `release-acceptance.json` for wheel hash, operation IDs, managed bindings and retained source receipts.
- Loopback fixtures served unmodified published assets: native first setup, explicit migration, repeated init and upgrade passed without manager discovery during reuse/upgrade.

## Checks

- TDD observed the raw-default readiness failure before changing ownership checks; added bounded status/receipt tests. Further observed failures covered ambient-root redirection, doctor state separation and Windows extended canonical paths before their fixes.
- Focused source/bootstrap/doctor/upgrade suites: **116 passed, 1 skipped**.
- Final doctor/adapter/bootstrap refinements: **55 passed**.
- Sync, hook, skill and process inspection suites: **112 passed, 3 skipped**.
- Real released-manager source retention integration: **3 passed**.
- Real provider loopback/bootstrap plus adapter run: **19 passed**.
- Final independent installed-package acceptance: **2 passed**.
- Broad `uv run pytest -q`: **539 passed, 16 skipped, 1 failed**. The failure is `tests/test_workset_installed.py::test_installed_multirepo_move_copy_and_retry`, at the existing Windows transfer-file replacement boundary. It reproduced in a focused rerun and in a separately extracted, independently installed unchanged HEAD baseline. No workset implementation was changed. This remains a baseline test limitation; the full suite is not claimed green.
- `uv lock --check`, `git diff --check`, and `openspec validate adopt-saucepan-managed-setup --strict --no-interactive` pass.
- Unix native installer execution was not performed here; platform selection and command construction are covered locally, while this installed-package acceptance is Windows x64 only.

## Isolation incident and recovery

An initial installed-package test set HOME/USERPROFILE but omitted ZuAT's separate registry root. Three failed test runs appended 12 observe/install records to the existing ZuAT registry and changed its projection; native hook installation was rejected as conflicting. The native skill destinations were temporary homes. The fixture now explicitly isolates `ZUAT_HOME`, `LOCALAPPDATA`, `APPDATA`, `HOME`, `USERPROFILE` and `CODEX_HOME`.

After confirming the registry had no unrelated edits or intervening commits, the test-created history was backed up to `build/managed-setup/zuat-isolation-recovery.bundle`. Its active HEAD and projection were restored exactly to pre-test commit `8c1039c`. The corrected installed acceptance was rerun successfully. Hash comparisons confirmed the real Saucepan executable/root marker, Codex hook file, original consumer config/receipts and restored ZuAT HEAD were unchanged across the corrected final runs. No real-home Saucepan migration occurred. The early isolation failure is reported rather than claiming that no home write ever occurred.

## Checkpoint

Reviewed the scoped diff and proposed commit subject: `Adopt Saucepan managed setup for default source clients`. The selected `zmem` is the legacy Python/service runtime, without the Node engine's file-based proposal validation; computed-memory commit validation was unavailable. No new runtime was installed and no Powerspec commit was created. Archive/sync and a consumer release/version decision remain separate follow-up actions.

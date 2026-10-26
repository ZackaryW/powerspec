# Tasks

## 1. Restructure long requirements

- [x] 1.1 Write delta specs for all 13 capabilities so every flagged requirement is 500 characters or fewer, and verify each delta with `openspec validate split-long-requirements --strict`
- [x] 1.2 Verify no rewritten clause lost its normative keyword where the original had one, using a clause-level SHALL/MUST/MAY scan of every rewritten requirement

## 2. Verify preservation before sync

- [x] 2.1 Trial-sync the deltas onto a scratch copy of `openspec/specs` and verify `openspec validate --specs --strict` passes for all 17 specs
- [x] 2.2 Verify on the trial copy that all 544 original scenarios survive verbatim, untouched requirements are byte-identical, and spec headers and purposes are unchanged

## 3. Publish

- [x] 3.1 Sync the deltas into `openspec/specs`, rerun the preservation check against the committed baseline, and verify `openspec validate --specs --strict` passes 17 of 17

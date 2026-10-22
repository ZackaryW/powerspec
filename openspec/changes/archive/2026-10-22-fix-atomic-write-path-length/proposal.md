## Why

Workset change transfer can fail on Windows even when its receipt destination is a valid path, because the shared atomic writer makes a longer temporary filename from the entire destination basename. The installed multi-repository move/copy/retry test reproduces this on the unchanged baseline; isolated experiments confirm that a short temporary name removes the failure.

## What Changes

- Use a short, destination-independent temporary basename in the existing shared atomic writer, retaining exclusive temporary creation in the destination directory and atomic replacement.
- Preserve unchanged-content no-ops, previous contents on publication failure, temporary-file cleanup, and existing error handling.
- Specify that valid workset receipt destinations must not fail solely because staging repeats their long basename; preserve receipt identity, layout, and retry compatibility.
- Add focused path-boundary and cleanup regression coverage and verify the installed workset workflow under its ordinary temporary root.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workset-launch`: Retaining transfer progress evidence must support valid receipt destinations without unnecessary staging-name expansion, while preserving safe partial progress and retries.

## Impact

- Implementation: `src/powerspec/utils/atomic.py`; shared callers in configuration, temporary state, syncing, sources, workset stores, and workset transfer retain their existing API.
- Tests: `tests/test_atomic.py` and installed workset/transfer coverage. Existing cleanup assertions must detect leaked files independently of the old temporary naming convention.
- No new dependency, receipt migration, CLI change, global Windows policy change, or general promise of support for paths beyond the host filesystem/API limits.

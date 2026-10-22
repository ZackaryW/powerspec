# Implementation verification

Verified on Windows on 2026-10-22 using the pinned Saucepan v0.11.0 raw
manager and checksum-verified official release assets. Native fixtures use
disposable homes, stores and local Git origins, not the user's ready store.

## Retrieval and selection observations

`tests/test_source_cache_integration.py` observes Git trace events and retained
revisions through the real manager. Its CLI smoke exercises the actual init
handler with an isolated provider client.

| Operation | Git retrieval observed | Selection result |
| --- | --- | --- |
| Cold init | Yes | Initial revision retained |
| Repeated ordinary init | None | Exact original revision retained |
| Second consumer with warm cache | None | Same revision, independent retention |
| New consumer at 86399 seconds | None | Cached revision retained |
| New consumer at 86400 seconds | Yes | Updated upstream revision selected |
| Future-dated freshness evidence | Yes | Retrieval required |
| Warm cache while origin is offline | None | Initialization succeeds |
| Expired cache while origin is offline | Required, fails | No selection published |
| Forced init after upstream commit | Yes | Requesting consumer advances; other pin unchanged |
| Failed forced retrieval | Required, fails | Previous successful selection preserved |

Provider clock injection is test-only. No test asserts a latency threshold.
Cache reuse still involves local policy registration, output preparation and
validation; copying and hashing costs are separate from upstream retrieval.
This change does not optimize those provider operations or claim transfer
telemetry that the provider does not expose.

## Installed distribution

Rebuilt and installed the working tree with `uv tool install --force .`.
The independently installed `pspec init --help` exposes all three force effects.
`tests/test_installed_managed_setup.py`: **2 passed in 30.95 seconds**.
Both cases use isolated homes and exercise setup, repeated init, doctor and
upgrade. The unmanaged case now uses `init --agent codex --force` and verifies
the migration backup hash, preserved operation ID and ready managed status.
The timing is diagnostic for the complete acceptance cases, not cache latency.

## Complete suite

`uv run pytest -q --tb=short` with `SAUCEPAN_TEST_BINARY`,
`SAUCEPAN_RELEASE_ASSETS` and `POWERSPEC_TEST_ENTRYPOINT` set:
**632 passed, 11 skipped in 324.38 seconds**. The skips are remaining opt-in
or platform-specific cases; native source/setup and installed Windows acceptance
cases were enabled. An outdated workspace test double found in the first run
was updated to accept and assert independent migration consent; its focused
workspace/CLI/bootstrap follow-up passed all 18 tests before the final full run.

## Contract review

- `remote-sources`: manager-expanded 86400-second freshness, stable pending
  intent, independent pins, explicit refresh and failure retention are covered
  by source unit tests and native trace tests.
- `managed-saucepan-binary`: default-off consent, observed digest, official
  installer, provider rejection, standalone bypass, ready reuse and stable
  recovery identities are covered by adapter and disposable installer tests.
- `cli-product-surface`: explicit agent scope, guarded receipt repair,
  preservation of edited assets, invalid-agent early failure, operation reporting
  and truthful progress are covered by CLI, installation, hook and progress tests.

Final migration-guidance follow-up: **32 passed** across source-tool, managed
setup contract and forced-migration tests. Strict OpenSpec validation and
`git diff --check` passed. Computed zmem message validation was unavailable:
the installed runtime is the older Python/service interface, not the required
TypeScript/Node engine. Local commits use ordinary messages without memory
annotations; no push or release was performed.

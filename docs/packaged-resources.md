# Packaged resources

Powerspec distributions contain the complete builtin `.pspec` catalog. Normal
builds, installations, `pspec init`, `pspec sync`, and `pspec skill` resolution
read that snapshot locally. They do not fetch OpenSpec skills or generate missing
resources.

ZuAT and Zuu are pinned Git dependencies in the distribution metadata as well as
the uv lockfile. A wheel installer therefore resolves the same revisions without
depending on a checkout's uv source configuration. Installing dependencies may
access their Git sources; provisioning the packaged OpenSpec skills uses the
local catalog.

The vendored OpenSpec skill snapshot is recorded in
`.pspec/skills/UPSTREAM_PROVENANCE.md`; its license is retained in
`.pspec/skills/UPSTREAM_LICENSE.txt`. Refreshing it is a maintainer operation:

1. Select an OpenSpec tag compatible with the supported OpenSpec CLI.
2. Copy each complete selected `skills/<name>` directory, including references
   and scripts, into `.pspec/skills/<name>`.
3. Update the pinned tag, commit, source paths, and compatibility statement in
   `UPSTREAM_PROVENANCE.md`, and refresh the upstream license when necessary.
4. Run the resource tests and build both distribution formats with `uv build`.
5. Rebuild a wheel from the sdist with `uv build --offline --wheel <sdist>` and
   compare its archive entries with the directly built wheel.

If an installation lacks its packaged catalog, Powerspec reports a configuration
error. Reinstall or repair the distribution; runtime fallback to a network source
is deliberately unsupported.

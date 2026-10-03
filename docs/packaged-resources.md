# Packaged resources

Powerspec distributions contain the complete builtin catalog. Normal
installations, `pspec init`, `pspec sync`, and `pspec resolve skill` read that
snapshot locally. Runtime commands never fetch OpenSpec skills or generate
missing resources.

Powerspec-authored profiles, contexts, traits, and skills remain under `.pspec`.
The OpenSpec repository, immutable commit, selected skill roots, and license path
are declared under `[tool.hatch.build.hooks.custom.source]` in `pyproject.toml`.
They are not copied into `.pspec/skills`.

The Hatch build hook uses Zuu's pinned GitHub-subpath materializer to stage only
the declared complete skill roots. It rejects missing or redirected paths,
identity mismatches, and invalid revisions. It adds generated license,
provenance, and content digests to the build snapshot. Direct wheels receive the
validated skills through Hatch's `force_include` boundary.

An sdist carries the validated snapshot under `powerspec_build/openspec`. A wheel
built from that sdist validates its digest manifest and reuses it without network
access. To verify parity:

1. Run `uv build --wheel --out-dir <direct>`.
2. Run `uv build --sdist --out-dir <source>`.
3. Run `uv build --offline --wheel <source>/powerspec-*.tar.gz --out-dir <rebuilt>`.
4. Compare all `powerspec/_resources/catalog/` paths and bytes in both wheels.

`POWERSPEC_OPENSPEC_SOURCE` is a build-test override for a prepared OpenSpec
checkout. Normal builds leave it unset so the immutable public declaration is
actually reproduced.

If an installation lacks its packaged catalog, Powerspec reports a configuration
error. Reinstall or repair the distribution; runtime fallback to a network source
is deliberately unsupported.

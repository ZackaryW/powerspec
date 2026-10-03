# Temporary state cleanup

`openspec/.pspec/current.toml` contains gitignored runtime answers. Tracked
`config.toml` contains persistent choices. Both accept shared `[vars]` and
direct change-specific `[_change.<name>]` tables, but only `current.toml` is a
flush target.

After successfully archiving one OpenSpec change, clear only that change's
temporal layer:

```console
pspec flush --change archived-change-name
```

The command resolves the nearest owning consumer inside the current Git or
worktree boundary. It removes that direct change table while retaining shared
runtime values, other change tables, comments, and formatting. A missing file
or absent change is an `unchanged` success. Run it only after archive success;
a failed or cancelled archive keeps its runtime answers. Cleanup failure is
reported separately and does not reverse or misreport the archive.

To clear every temporal answer for the consumer:

```console
pspec flush
```

When state exists, the full form leaves the canonical empty surface:

```toml
[vars]
```

A missing file is not created. Both forms validate a present document before
editing it, validate the rendered candidate, and replace only `current.toml`
through a sibling staging file. Invalid TOML, unsupported tables, or publication
failures return a nonzero diagnostic and preserve the original bytes.

The global builtin context publishes the post-success archive instruction into
`operations.archive.guidance` on the next `pspec sync`. Flush does not invoke
OpenSpec archive, infer an active change, edit `config.toml` or `config.yaml`, or
touch skills and hooks.

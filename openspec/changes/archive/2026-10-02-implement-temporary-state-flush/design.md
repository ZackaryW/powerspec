# Design

## Context

See proposal.md. Consumer discovery and the persistent/temporary variable model
already exist. `current.toml` is gitignored and may contain `[vars]` plus direct
`[_change.<name>]` tables. The public flush command is the remaining placeholder.

## Goals / Non-Goals

**Goals:** Provide a small idempotent lifecycle operation with an explicit
change-scoped form, round-trip preservation for targeted cleanup, complete
validation before publication, and atomic replacement.

**Non-Goals:** Infer an active change, invoke OpenSpec archive, edit
`config.toml` or `config.yaml`, clean agent installations, retain a history of
temporal answers, or guarantee cross-process locking.

## Decisions

### Reuse consumer discovery without loading runtime state

Discover the owning consumer with `runtime=False`, then inspect its adjacent
`current.toml` in the cleanup service. This retains Git/worktree boundaries and
lets a missing file be an idempotent success while a present malformed file is
diagnosed at the mutation boundary.

Alternative rejected: use the process or package location. User-level commands
serve multiple repositories and cannot safely infer ownership that way.

### Use TOMLKit for validated targeted edits

Parse the present document with TOMLKit, validate its unwrapped value through
the existing strict `Variables` model, and delete the selected direct change key
from the round-trip document. Remove an empty `_change` container. This
preserves shared values, other changes, comments, and formatting without a
home-grown TOML parser. Declare TOMLKit as a direct dependency.

Alternative rejected: serialize through a custom writer. Temporal values can
contain native TOML types and the targeted operation must retain unrelated
authored state.

### Full reset uses one canonical document

When any temporal values exist, the no-argument form publishes exactly an empty
`[vars]` table. If validated state is already empty, return unchanged and retain
the original file. A missing file is also unchanged; flush never creates state
merely to record emptiness.

### Validate and stage before replacement

Render and reparse the candidate, validate it again, write a sibling temporary
file, flush it to disk, and replace `current.toml` with `os.replace`. Any failure
before replacement retains the original bytes. Report `updated:` or
`unchanged:` only after the corresponding result is known.

### Archive remains the caller

The archive workflow runs `pspec flush --change <name>` only after archive
success. Flush itself knows no OpenSpec archive semantics, so a failed or
cancelled archive never triggers cleanup. This keeps the command reusable and
prevents it from claiming archive success.

Publish that handoff from a global builtin context at
`operations.archive.guidance`. Sync remains the only writer of `config.yaml`;
flush never edits the compiled instruction. The managed guidance tells the
agent to report cleanup failure separately after a successful archive.

## Risks / Trade-offs

- Concurrent writers can still race around the final replacement: keep the
  operation atomic and document last-writer behavior rather than add a lock
  protocol in this milestone.
- Full reset intentionally discards comments with nonempty temporal state:
  targeted cleanup remains the preservation-oriented path used by archive.
- TOMLKit adds one runtime dependency: pin a compatible range and cover its
  round-trip behavior with focused tests.

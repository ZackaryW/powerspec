# Skill installation

Profile composition produces a plan containing each skill's qualified identity,
source directory, declaring profile, agent, scope, and project root. Provisioning
passes these explicit targets to ZuAT. A project's source catalog is never used
as its native installation destination.

One profile has one installation scope. Its skills default to `user`; a profile
with `scope = "project"` requires the target repository root. Composed profiles
retain their own scopes, so a user-level builtin profile and a project-level
application profile can coexist. The host agent chooses which installed copy it
uses at runtime.

Powerspec inspects each target before installing. Matching managed copies are
reused, and a completely inspected byte-identical unowned copy is adopted without
rewriting it. Differing unmanaged or edited copies and unsupported scopes produce
failures with diagnostics. When plugin inventory prevents complete inspection, read-only native
lookup must establish that no copy at the requested scope is being adopted;
ZuAT then performs its own non-forced installation checks.

`pspec upgrade --agent <agent> --force` explicitly permits ZuAT to archive and
replace selected differing unowned or locally modified skills. Force applies only
to selected skill provisioning. It does not bypass incomplete inspection, change
hook ownership, or weaken obsolete-skill removal checks.

Provisioning returns a result for every planned skill. Successful earlier actions
remain installed if a later action fails. Resolve the reported conflicts and rerun
`pspec init --agent <agent>`; matching completed installations will be reused. Powerspec does
not claim rollback or complete readiness after a partial failure.

The entire skill directory is installed, including manifests and currently
inactive branches. Changing a runtime variable does not require reinstallation.
Removing a profile from the effective bundle removes its contributions for that
consumer; it does not uninstall shared skills or disable their native discovery.

## Make scenario skills available without native installation

Use `resolve-skills` in an authored profile for targets that should remain out of native discovery. Keep bootstrap in `skills`. A lightweight context or trait can say `When the task needs a test-first cycle, use pspec:@builtin/pspec-tdd`; its condition decides when retrieval is needed. This literal reference does not retrieve the procedure during publication or hook rendering. Native `<skill:name>` tokens require installation selections; exclusively resolve-only names receive an authoring diagnostic.

```toml
# openspec/.pspec/profiles/scenarios.toml
skills = ["@builtin/pspec-skill-bootstrap"]
resolve-skills = ["@builtin/pspec-tdd"]
contexts = ["@local/scenarios"]
```

Select this profile with the consumer's existing `profile = "@local/scenarios"`. No `resolve-skills` field is added to consumer config. Init/upgrade prepare sources for both lists, but only `skills` creates ZuAT targets. Switching a declaration to resolve-only or excluding it does not remove an existing native copy; context reduction applies to fresh installations with this delivery choice.

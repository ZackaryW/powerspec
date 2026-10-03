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
reused. Unmanaged or edited copies and unsupported scopes produce failures with
diagnostics. When plugin inventory prevents complete inspection, read-only native
lookup must establish that no copy at the requested scope is being adopted;
ZuAT then performs its own non-forced installation checks.

Provisioning returns a result for every planned skill. Successful earlier actions
remain installed if a later action fails. Resolve the reported conflicts and rerun
`pspec init --agent <agent>`; matching completed installations will be reused. Powerspec does
not claim rollback or complete readiness after a partial failure.

The entire skill directory is installed, including manifests and currently
inactive branches. Changing a runtime variable does not require reinstallation.
Removing a profile from the effective bundle removes its contributions for that
consumer; it does not uninstall shared skills or disable their native discovery.

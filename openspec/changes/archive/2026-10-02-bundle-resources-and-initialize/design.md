# Design

## Context

See proposal.md. Packaging currently uses uv_build; .pspec contains reviewed sources, not a distribution resource loader. The CLI init handler is a placeholder. Prerequisites are establish-profile-consumer-resolution and implement-skill-content-resolution, including the incremental cli-scaffold contract.

ZuAT 0.1.0 inspection found explicit user/project skill scopes and public inspection/install operations. Its default agent list includes all agents, so every request must set the target explicitly. Those API observations still need exercised integration evidence.

## Goals / Non-Goals

**Goals:** Complete resources available from an installed distribution, scoped installation, and repeatable Git-root repository initialization.

**Non-Goals:** Runtime skill filtering during installation, network-based OpenSpec provisioning, native hook registration (next change), remote source management, sync compilation, or flush.

## Decisions

### Maintainers prepare upstream resources; users install locally

Vendor selected committed skills/<name>/ directories from a pinned compatible Fission-AI/OpenSpec revision with full resources, license, and repository/commit/path provenance. The upstream repository already distributes ready-to-install skill files. Its generation scripts are upstream maintenance, not Powerspec build/init steps.

Use Hatchling for wheel/sdist inclusion; retain uv as frontend and uv run pytest. Load installed package resources without source-checkout or cache assumptions. Prove a wheel rebuilt offline from sdist, with build dependencies available, has equivalent selected resources and attribution.

This replaces runtime OpenSpec fetching. Saucepan inspection showed a full repository materialization before folder selection; selecting skills alone does not avoid that acquisition. User-added remote sources are a separate change. Ordinary builds/init must neither fetch upstream nor regenerate skills, even as a fallback for missing resources.

### Installation consumes composition, not runtime answers

Use effective resource/target descriptors from profile composition. All referenced resources and inactive branches stay installed. Preserve each declaring profile's scope; user defaults remain user, project requires the target repository root as project_root. A source catalog path is not the project target.

Reuse the skill change's explicit-agent ZuAT boundary for inspection and add provisioning operations. Expose identities, provenance, agent, and scope in the plan. Inspect before writes; matching targets are reused, unmanaged/locally edited targets conflict, unsupported scopes fail rather than switching. Report completed and failed actions separately on partial failure; do not claim transactional rollback.

Profile exclusion does not uninstall shared resources. ZuAT artifact enabled/disabled policy does not guarantee native skill activation control. Native agents still own runtime user/project selection.

### Initialization creates a consumer and provisions the selected bundle

Detect the Git root, including worktree boundaries, and bootstrap OpenSpec without its repository skill generation. Preserve existing consumer config and native skills. Establish openspec/.pspec configuration and a current.toml ignore rule without ignoring config.toml or the whole directory; do not claim an ignored tracked file became untracked.

Use the reviewed profile selection and require an identified supported target agent before provisioning. The scaffold's optional --agent syntax does not authorize an implicit all-agent default; unresolved identity is diagnosed. User-scoped OpenSpec/bootstrap/TDD creates no repository skill copies. A project-scoped profile may explicitly install its skills locally.

For a fresh consumer, optional `--profile <qualified-reference>` supplies the initial selection. Later runs use config.toml. A different explicit selector conflicts with an existing selection instead of replacing it; users change persistent selection by editing the consumer. Missing or empty profile selection mounts only global profiles after exclusions. This same composition applies to initialization, sync, and runtime resolution; it never implies an empty bundle unless all global contributions are excluded.

Runtime trait resource parsing is already available, but generic callback registrations are added only by implement-trait-hook-delivery. This milestone reports installation availability and does not claim bootstrap was delivered or followed. It also does not synthesize compiled context publication into config.yaml; implement-context-sync owns that independent milestone.

## Risks / Trade-offs

- Dependency/API compatibility changes → pin compatible ZuAT/OpenSpec revisions and verify in disposable homes.
- Hidden build dependency on a checkout or network → install and test outside the repository, then rebuild offline from sdist.
- Partial filesystem completion → preserve successful actions and report exact failures, without automatic deletion of shared skills.

## Migration Plan

Prepare the pinned upstream snapshot, switch backend/resource inclusion, and verify distribution contents. Add scoped provisioning, implement init, then demonstrate repeated initialization and two consumers using different branches of one complete installation.

Only disposable homes/projects are used for tests. Reverting a package does not automatically remove shared native installations; report installed resources so explicit recovery remains possible. Completion includes ordinary OpenSpec null fallback through the real skill command and no network dependency for bundled initialization.

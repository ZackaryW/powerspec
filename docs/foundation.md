# Resolution foundation

The catalog library reads authored resources without installing, executing, or publishing them. Installation, skill resolution, and context publication use that shared foundation through their own commands.

Omitting the selected profile, or declaring `profile = ""`, composes the global profiles after consumer exclusions. The selected-profile default tier stays empty. Init, sync, and runtime resolution use this same global-only bundle.

`Catalog(builtin=...)` explicitly injects the Powerspec catalog. `sources={"local": consumer_path}` registers private consumer resources; other keys register already-materialized reusable catalogs. External registration cannot use `builtin`. `gitsources` accepts already-materialized source roots for downstream adapters; it does not fetch or register a Saucepan source.

Profiles reference `contexts`, `traits`, `skills`, and subprofiles through qualified string lists. A profile can also declare `[[source]]` entries containing a friendly `id` and an exact Git `provider`, `origin`, and `reference`; these recipes satisfy matching `@gitsource/<id>/...` skill selectors. Contexts own compile-time inputs and `attach` destinations; traits own runtime `hooks`, `body`, and optional Python `when`. Legacy modes/check tables and mixed kinds are rejected. Skill identity comes from YAML frontmatter `name`, independently of its directory name. Duplicate names within a source fail. Context and trait names occupy separate namespaces.

Catalog parsing checks condition syntax only. It does not execute callbacks. Skill manifests keep their independent dynamic guard contract. Remote skill selectors select materialized immediate child roots with `*` or descendants with `**`; returned resources retain exact source-relative identities.

TOML decoding uses `tomllib`; authored profile, context, trait, and consumer shapes use strict Pydantic v2 models with unknown fields rejected. Compile-time defaults and choices must match their declared type. Variable tables remain open mappings of native values. Graph composition, identity checks, precedence, and Zuu expression evaluation remain separate application rules. These models do not implement the later skill-manifest resolver.

Utilities in `powerspec.utils` take ordinary caller-owned data: bounded paths, ordered dependency mappings, named value layers, or literal command arguments. They contain no Git, OpenSpec, or profile policy. Filesystem/process effects and errors are documented in each helper.

## Compose an effective bundle

```python
from powerspec.catalog import Catalog
from powerspec.profiles import compose

catalog = Catalog(builtin=authoring_root)
bundle = compose(catalog, "@builtin/python-simple-cli", agent="codex",
                 exclude_profiles=["@builtin/zmem-lifecycle", "@builtin/adhd-friendly"])
```

The excluded examples require external materializations; omission here is explicit fixture configuration, not implicit tolerance of missing selected sources. Production composition fails on missing selected resources. The reviewed Python fixture includes utility contexts, bootstrap, utility planning, and one TDD target without BDD.

Only consumer and explicitly selected root `exclude-profiles` prune the graph. A shared descendant still reached elsewhere survives. Globals and subprofiles mount once. Profiles reached from the selected root supply selected-tier defaults; globals-only reachability supplies the global tier. Unequal same-tier defaults fail rather than acquiring precedence from graph depth. Excluding a profile changes selection only; no installed files are removed.

Each declaring profile retains its user/project skill scope. `project_root` is mandatory for a project-scoped skill. Targets with different scopes coexist; different resources competing for the same agent/name/scope/root fail. The native agent still owns which installed copy it invokes.

## Consumer variables

`discover_consumer(cwd)` selects the nearest owning `openspec/.pspec/config.toml` inside the enclosing Git boundary, including worktree `.git` files and calls inside OpenSpec. A malformed nearest file fails. No consumer returns `None`, without parent-repository, sibling, home-directory, or authoring-source fallback.

Persistent `config.toml` and temporary, gitignored `current.toml` use the same variable structure:

```toml
[vars]
language = "python"

[_change.fix-output]
test_command = "uv run pytest tests/test_output.py"
```

`runtime_values(consumer, bundle, change="fix-output", defaults={})` returns values and their winning origins. From low to high precedence: caller skill defaults, global profiles, selected profiles, config shared, config matching change, current shared, current matching change. Omitting `change` uses shared layers only. No change is inferred and no other change table contributes.

For compilation use `discover_consumer(cwd, runtime=False)` and `context_values(resource, consumer, bundle)`. This ignores even a malformed `current.toml`; only declaration defaults, global/selected defaults, and persistent shared values participate. Invalid supplied values fail instead of falling back; required missing values never prompt. These functions create no state files and write no configuration. Archive cleanup is an explicit later `pspec state clear --change <name>` operation against `current.toml`; it never participates in value resolution.

## Guidance conditions

`Invocation(cwd, env=...)` captures the invoking working directory, environment, and Git root. `evaluate(when, values=..., bundle=..., invocation=..., location=...)` uses the pinned Zuu case18 expression evaluator with empty builtins and direct-dunder guarding. A condition must return an actual Boolean. Ordinary bodies/defaults remain data.

The bindings are `vars` (a read-only top-level mapping), `git_root` (an invocation-owned Path, unavailable outside Git), `which(name)`, `run_json(argv)`, and `armed(kind, reference)`. Variables cannot replace capability names. Executable lookup honors invocation-relative paths and its PATH/PATHEXT without changing process cwd or environment. This small invocation adapter is necessary because `shutil.which` reads process-global PATHEXT and cwd. A probe requires a nonempty argument list, no shell, exit zero, an object JSON result, and a five-second subprocess timeout. `ok=false` remains data; successful exit alone is not readiness.

`armed` reports selection after exclusions for an exact profile/context/trait/skill identity. It does not check installation, condition results, or whether a workflow is active. Selected globals and subprofiles participate; shared descendants remain selected through surviving paths. Remote wildcard contributions retain exact source-relative identities, but queries cannot contain wildcards or acquire missing sources. Self/mutual queries require no recursive evaluation.

`context_contributions` prepares a complete compile-time snapshot with destination, body, values, and origins. `trait_contributions(..., matching_refs=..., change=...)` evaluates only selected traits matched by the delivery caller. The [runtime hook adapter](hook-delivery.md) owns native event normalization and response serialization. Both return a completed tuple or raise a located diagnostic, never a successful partial payload. False omits one contribution without altering selection. Rebuild invocation, consumer, and bundle snapshots on each later command; no results are persisted here.

Conditions are trusted executable rules, not isolated code. Case18 restrictions do not confine Path methods or callbacks. Nested variable objects retain their normal semantics. There is no evaluator-wide time/memory limit or rollback; the timeout bounds only the subprocess. Powerspec's own resolution does not publish or install anything, but arbitrary authored expressions can have host effects. Tests use disposable fixtures and controlled probes.

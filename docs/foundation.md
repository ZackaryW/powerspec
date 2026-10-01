# Resolution foundation

The catalog library reads authored resources without installing, executing, or publishing them. CLI domain commands remain placeholders until their respective changes land.

`Catalog(builtin=...)` explicitly injects the Powerspec catalog. `sources={"local": consumer_path}` registers private consumer resources; other keys register already-materialized reusable catalogs. External registration cannot use `builtin`. `gitsources` accepts already-materialized source roots for downstream adapters; it does not fetch or register a Saucepan source.

Profiles reference `contexts`, `traits`, `skills`, and subprofiles through qualified string lists. Contexts own compile-time inputs and `attach` destinations; traits own runtime `hooks`, `body`, and optional Python `when`. Legacy modes/check tables and mixed kinds are rejected. Skill identity comes from YAML frontmatter `name`, independently of its directory name. Duplicate names within a source fail. Context and trait names occupy separate namespaces.

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

For compilation use `discover_consumer(cwd, runtime=False)` and `context_values(resource, consumer, bundle)`. This ignores even a malformed `current.toml`; only declaration defaults, global/selected defaults, and persistent shared values participate. Invalid supplied values fail instead of falling back; required missing values never prompt. These functions create no state files, write no configuration, and perform no archive cleanup.

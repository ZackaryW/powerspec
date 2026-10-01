# Resolution foundation

The catalog library reads authored resources without installing, executing, or publishing them. CLI domain commands remain placeholders until their respective changes land.

`Catalog(builtin=...)` explicitly injects the Powerspec catalog. `sources={"local": consumer_path}` registers private consumer resources; other keys register already-materialized reusable catalogs. External registration cannot use `builtin`. `gitsources` accepts already-materialized source roots for downstream adapters; it does not fetch or register a Saucepan source.

Profiles reference `contexts`, `traits`, `skills`, and subprofiles through qualified string lists. Contexts own compile-time inputs and `attach` destinations; traits own runtime `hooks`, `body`, and optional Python `when`. Legacy modes/check tables and mixed kinds are rejected. Skill identity comes from YAML frontmatter `name`, independently of its directory name. Duplicate names within a source fail. Context and trait names occupy separate namespaces.

Catalog parsing checks condition syntax only. It does not execute callbacks. Skill manifests keep their independent dynamic guard contract. Remote skill selectors select materialized immediate child roots with `*` or descendants with `**`; returned resources retain exact source-relative identities.

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

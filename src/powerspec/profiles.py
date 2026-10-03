"""Profile graph policy and installation descriptors, without installation."""
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from collections.abc import Mapping
from .catalog import Catalog, ConfigurationError, Resource, KINDS, reference
from .utils.dependencies import dependency_order


@dataclass(frozen=True)
class SkillTarget:
    resource: Resource
    agent: str
    scope: str
    project_root: Path | None
    profile: str


@dataclass(frozen=True)
class Bundle:
    profiles: tuple[Resource, ...]
    contexts: tuple[Resource, ...]
    traits: tuple[Resource, ...]
    skills: tuple[SkillTarget, ...]
    sources: Mapping
    selected_defaults: Mapping
    global_defaults: Mapping
    selection: frozenset[tuple[str, str]]

    def armed(self, kind: str, ref: str) -> bool:
        if not isinstance(kind, str) or kind not in KINDS:
            raise ConfigurationError(f"invalid resource kind: {kind!r}")
        return (kind, reference(ref, wildcard=kind == "skill")) in self.selection


def compose(catalog: Catalog, selected: str | None = None, *, agent: str, project_root: Path | None = None,
            exclude_profiles=(), resolve_skills: bool = True,
            resolve_remote_skills: bool = True, empty_skill_selectors=()) -> Bundle:
    """Compose the selected root and globals after explicit exclusions.

    Only consumer and selected-root exclusions apply. Scope stays with each
    declaring profile; reachability selects one of two default tiers.
    """
    if not isinstance(agent, str) or not agent.strip():
        raise ConfigurationError("an explicit target agent is required")
    if isinstance(exclude_profiles, (str, bytes)):
        raise ConfigurationError("exclude_profiles must be a sequence of qualified references")
    if isinstance(empty_skill_selectors, (str, bytes)):
        raise ConfigurationError("empty_skill_selectors must be a sequence of qualified references")
    allowed_empty = {reference(item, wildcard=True) for item in empty_skill_selectors}
    selected = selected or None
    root = catalog.get("profile", selected) if selected is not None else None
    excluded = {reference(x) for x in exclude_profiles} | set(root.data.get("exclude-profiles", []) if root else [])
    if selected in excluded:
        raise ConfigurationError(f"explicitly selected profile is excluded: {selected}")
    globals_ = [r.ref for (kind, _), r in catalog.resources.items()
                if kind == "profile" and r.data.get("global", False) and r.ref not in excluded]
    roots = list(dict.fromkeys([*globals_, *([selected] if selected else [])]))
    graph, resources = {}, {}
    pending = [(name, (name,)) for name in reversed(roots)]
    while pending:
        name, chain = pending.pop()
        if name in graph:
            continue
        try:
            resource = catalog.get("profile", name)
        except ConfigurationError as error:
            raise ConfigurationError(f"{' -> '.join(chain)}: {error}") from error
        resources[name] = resource
        children = [child for child in resource.data.get("profiles", []) if child not in excluded]
        graph[name] = children
        pending.extend((child, (*chain, child)) for child in reversed(children))
    try:
        order = dependency_order(roots, graph)
        selected_reachable = set(dependency_order([selected], graph)) if selected else set()
    except ValueError as error:
        raise ConfigurationError(str(error)) from error
    defaults = {"selected": {}, "global": {}}
    owners = {"selected": {}, "global": {}}
    sources, source_owners = {}, {}
    for identity in order:
        for declaration in resources[identity].data.get("source", []):
            source = declaration["id"]
            recipe = {key: declaration[key] for key in ("provider", "origin", "reference")}
            if source in sources and sources[source] != recipe:
                raise ConfigurationError(
                    f"source alias conflict for {source}: {source_owners[source]} and {identity}"
                )
            sources[source] = recipe
            source_owners[source] = identity
    catalog.set_git_recipes(sources)
    contexts, traits, targets, names, deferred_skill_refs = {}, {}, {}, {}, []
    for identity in order:
        resource = resources[identity]
        data = resource.data
        tier = "selected" if identity in selected_reachable else "global"
        for key, value in data.get("vars", {}).items():
            if key in defaults[tier] and (type(value) is not type(defaults[tier][key]) or value != defaults[tier][key]):
                raise ConfigurationError(f"default conflict for {key}: {owners[tier][key]} and {identity} ({tier} tier)")
            defaults[tier][key] = value
            owners[tier][key] = identity
        for kind, destination in (("context", contexts), ("trait", traits)):
            for ref in data.get(kind + "s", []):
                try:
                    item = catalog.get(kind, ref)
                except ConfigurationError as error:
                    raise ConfigurationError(f"{identity}: {error}") from error
                destination.setdefault(item.ref, item)
        scope = data.get("scope", "user")
        for ref in data.get("skills", []):
            if not resolve_skills or (not resolve_remote_skills and ref.startswith("@gitsource/")):
                deferred_skill_refs.append(ref)
                continue
            if scope == "project" and project_root is None:
                raise ConfigurationError(f"{identity}: project scope requires explicit project_root")
            target_root = Path(project_root).resolve() if scope == "project" else None
            for item in catalog.select("skill", ref, allow_empty=ref in allowed_empty):
                destination = (agent, scope, target_root, item.name)
                if destination in names and names[destination] != item.ref:
                    raise ConfigurationError(f"skill target conflict: {names[destination]} and {item.ref} at {destination}")
                names[destination] = item.ref
                target = SkillTarget(item, agent, scope, target_root, identity)
                targets.setdefault((item.ref, agent, scope, target_root), target)
    profiles = tuple(resources[name] for name in order)
    selection = frozenset([(r.kind, r.ref) for r in (*profiles, *contexts.values(), *traits.values())]
                          + [("skill", t.resource.ref) for t in targets.values()]
                          + [("skill", ref) for ref in deferred_skill_refs])
    source_view = MappingProxyType({key: MappingProxyType(dict(value)) for key, value in sources.items()})
    return Bundle(profiles, tuple(contexts.values()), tuple(traits.values()), tuple(targets.values()), source_view,
                  MappingProxyType(defaults["selected"]), MappingProxyType(defaults["global"]), selection)

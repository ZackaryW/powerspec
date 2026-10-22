"""Select one effective catalog skill without provisioning or source acquisition."""
from dataclasses import dataclass
from pathlib import Path

from .catalog import ConfigurationError, NAME, skill_reference
from .resources import durable_skill_root
from .skills import manifest_supported, read_document, resolve_skill, SkillResolution


def select_catalog_skill(catalog, bundle, selector):
    exact = selector.startswith('@') or '/' in selector
    if exact:
        skill_reference(selector)
    elif not NAME.fullmatch(selector):
        raise ConfigurationError(f'invalid skill name or exact reference: {selector!r}; invocation wildcards are unsupported')
    declarations = tuple(dict.fromkeys((*bundle.skill_declarations(), *bundle.skill_declarations('resolve-skills'))))
    candidates = {}
    for ref in declarations:
        if exact:
            if '*' not in ref and ref != selector:
                continue
            if '*' in ref and not selector.startswith(ref.rsplit('/', 1)[0] + '/'):
                continue
        try:
            resources = catalog.select('skill', ref, distinct_names=False)
        except (ConfigurationError, OSError, ValueError) as error:
            raise ConfigurationError(f'incomplete selected skill evidence for {ref}: {error}; prepare sources with pspec init, or refresh with pspec upgrade') from error
        for resource in resources:
            if (resource.ref == selector if exact else resource.name == selector):
                candidates[resource.ref] = resource
    if not candidates:
        raise ConfigurationError(f'skill {selector!r} is not selected by the effective profiles')
    if len(candidates) > 1:
        raise ConfigurationError(f'ambiguous skill {selector!r}; use an exact --ref: ' + ', '.join(sorted(candidates)))
    return next(iter(candidates.values()))


@dataclass(frozen=True)
class CatalogSkillResult:
    name: str
    ref: str
    root: Path
    resolution: SkillResolution


def resolve_catalog_skill(workspace, selector, *, change=None):
    resource = select_catalog_skill(workspace.catalog, workspace.bundle, selector)
    root = durable_skill_root(resource.path)
    if manifest_supported(root):
        result = resolve_skill(root, workspace.bundle, workspace.consumer, change=change)
    else:
        result = SkillResolution('resolved', read_document('SKILL.md', root=root, entrypoint=True), (), {}, {})
    if result.status == 'resolved':
        content = f'Skill reference: `{resource.ref}`\nSource directory: `{root}`\n\n{result.content}'
        # Ordinary documents need the same stable final-newline protocol as assembly.
        result = SkillResolution('resolved', content.rstrip() + '\n', (), result.values, result.origins)
    return CatalogSkillResult(resource.name, resource.ref, root, result)

"""Catalog evidence and targeted handoff text for authored skill references."""
from time import monotonic
from .catalog import ConfigurationError, MetadataUnavailable, is_git_skill_reference
from .skills import manifest_supported


DYNAMIC_HANDOFF = (
    'When the guidance below calls for these skills, select each through your native '
    'skill integration. Before following its procedure, run '
    '`pspec resolve skill --path "<selected-skill-location>" --agent <current-agent>` '
    'from the task directory. Include `--change <name>` only for an explicitly active '
    'change. Follow returned content or pending-choice instructions; report errors '
    'without bypassing resolution.'
)
UNKNOWN_HANDOFF = (
    'Select these skills through your native integration. Check each selected copy '
    'for pspec.toml; if present, request its Powerspec content using '
    '`pspec resolve skill --path "<selected-skill-location>" --agent <current-agent>` '
    'from the task directory before following the procedure. Include `--change <name>` '
    'only for an explicitly active change. Otherwise follow its ordinary instructions.'
)


class SkillReferences:
    """One contribution batch; never a persistent index or native-copy selector."""

    def __init__(self, bundle, *, catalog=None, diagnostics=None):
        self.resources = {}
        for target in bundle.skills:
            self.resources.setdefault(target.resource.name, {})[target.resource.path] = target.resource
        self.classified = {}
        materialized = {t.resource.ref for t in bundle.skills}
        self.deferred = sorted(ref for kind, ref in bundle.selection
                               if kind == 'skill' and is_git_skill_reference(ref)
                               and ref not in materialized)
        self.catalog = catalog
        self.diagnostics = diagnostics
        self.inspected = False
        self.unavailable = False

    def _inspect_deferred(self):
        if self.inspected:
            return
        self.inspected = True
        deadline = monotonic() + 1.0
        failed_sources = set()
        for ref in self.deferred:
            source = ref.split('/', 1)[0]
            if source in failed_sources:
                continue
            try:
                if self.catalog is None:
                    raise MetadataUnavailable(f'{ref}: no read-only catalog inspection available')
                if monotonic() >= deadline:
                    raise MetadataUnavailable(f'{ref}: skill metadata inspection budget exhausted')
                for resource in self.catalog.select('skill', ref, allow_empty=True, deadline=deadline):
                    self.resources.setdefault(resource.name, {})[resource.path] = resource
            except MetadataUnavailable as error:
                self.unavailable = True
                failed_sources.add(source)
                if self.diagnostics is not None:
                    self.diagnostics.append(str(error))

    def classify(self, name):
        self._inspect_deferred()
        resources = self.resources.get(name, {})
        if not resources and not self.unavailable:
            raise ConfigurationError(f'unknown selected skill reference {name}')
        states = set()
        for path in resources:
            if path not in self.classified:
                self.classified[path] = manifest_supported(path.parent)
            states.add(self.classified[path])
        if len(states) > 1:
            raise ConfigurationError(f'conflicting skill classifications for {name}')
        # Positive manifest evidence already requires the handoff. Incomplete
        # remote evidence cannot establish ordinary behavior or name absence.
        if self.unavailable and True not in states:
            return 'unknown'
        return 'dynamic' if True in states else 'ordinary'

    def annotate(self, body, names):
        groups = {'dynamic': [], 'unknown': []}
        for name in names:
            state = self.classify(name)
            if state in groups:
                groups[state].append(name)
        sections = []
        for state, heading, handoff in (
            ('dynamic', 'Skills requiring dynamic resolution', DYNAMIC_HANDOFF),
            ('unknown', 'Skill metadata unavailable', UNKNOWN_HANDOFF),
        ):
            if groups[state]:
                sections.append(f'### {heading}: {", ".join(groups[state])}\n\n{handoff}')
        return '\n\n'.join([*sections, body])

"""Evaluate trusted guidance conditions; this is not an execution sandbox."""
import os
import re
import math
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from collections.abc import Mapping
from zuu.case18 import RestrictedExecutor
from .catalog import ConfigurationError, Resource, attachments
from .consumer import find_git_root, runtime_values, context_values
from .utils.processes import ProcessJSONError, run_json_object


DEFAULT_RUN_JSON_TIMEOUT = 5.0


class OperationalConditionError(ConfigurationError):
    """A runtime command probe failed to produce condition data."""


class Invocation:
    def __init__(self, cwd, *, env=None, probe=None,
                 run_json_timeout=DEFAULT_RUN_JSON_TIMEOUT):
        if (isinstance(run_json_timeout, bool)
                or not isinstance(run_json_timeout, (int, float))
                or not math.isfinite(run_json_timeout)
                or run_json_timeout <= 0
                or run_json_timeout > DEFAULT_RUN_JSON_TIMEOUT):
            raise ValueError(
                "run_json_timeout must be a finite positive number no greater than 5 seconds"
            )
        self.cwd = Path(cwd).resolve(strict=True)
        self.env = dict(os.environ if env is None else env)
        self.git_root = find_git_root(self.cwd)
        self.probe = run_json_object if probe is None else probe
        self.run_json_timeout = float(run_json_timeout)

    def which(self, name):
        """Lookup without mutating process cwd/environment, including PATHEXT."""
        if not isinstance(name, str) or not name or '\x00' in name:
            raise ValueError("which requires a nonempty executable name")
        env = {k.upper(): v for k, v in self.env.items()} if os.name == 'nt' else self.env
        command = Path(name)
        if command.parent != Path('.') or command.is_absolute():
            directories = [command.parent]
        else:
            path = env.get('PATH', os.defpath)
            directories = [Path(p) for p in path.split(os.pathsep)] if path else []
            if os.name == 'nt' and 'NoDefaultCurrentDirectoryInExePath'.upper() not in env:
                directories.insert(0, self.cwd)
        names = [command.name]
        if os.name == 'nt':
            extensions = [ext.rstrip('.') for ext in (env.get('PATHEXT') or '.COM;.EXE;.BAT;.CMD').split(';') if ext]
            names = [command.name + ext for ext in extensions]
            if any(command.name.lower().endswith(ext.lower()) for ext in extensions):
                names.insert(0, command.name)
        for directory in directories:
            for filename in names:
                candidate = self.cwd / directory / filename
                if candidate.is_file() and os.access(candidate, os.F_OK | os.X_OK):
                    return str(candidate.resolve())
        return None

    def run_json(self, argv):
        if not isinstance(argv, list) or not argv or any(not isinstance(a, str) or '\x00' in a for a in argv) or not argv[0]:
            raise ValueError("run_json requires a nonempty list of string arguments")
        return self.probe(
            argv, cwd=self.cwd, env=dict(self.env), timeout=self.run_json_timeout,
        )


def evaluate(when, *, values, bundle, invocation, location):
    if when is None:
        return True
    bindings = {'vars': MappingProxyType(dict(values)), 'armed': bundle.armed,
                'which': invocation.which, 'run_json': invocation.run_json}
    # An unavailable base fails only if the expression actually requests it.
    if invocation.git_root is not None:
        bindings['git_root'] = invocation.git_root
    try:
        result = RestrictedExecutor(builtins={}, block_dunder_names=True).evaluate(
            when, bindings, filename=str(location))
        if type(result) is not bool:
            raise ValueError("condition must return an actual Boolean")
        return result
    except ProcessJSONError as error:
        raise OperationalConditionError(f"{location}: {error}") from error
    except Exception as error:
        raise ConfigurationError(f"{location}: {error}") from error


@dataclass(frozen=True)
class Contribution:
    resource: Resource
    destination: str | None
    body: str
    values: Mapping
    origins: Mapping
    identifier: str | None = None


PLACEHOLDER = re.compile(r"<skill:([a-z0-9][a-z0-9-]*)>|<([A-Za-z_][A-Za-z0-9_]*)>")
ATTACHMENT_ID = re.compile(r"[a-z0-9][a-z0-9-]*")


def _compile_body(body, resource, values, bundle):
    declared = {item['id'] for item in resource.data.get('compiletime', [])}
    skills = {target.resource.name for target in bundle.skills}
    # Runtime dispatch may intentionally defer remote skill materialization.
    # Exact selected references still establish the authored skill identity;
    # wildcards do not fabricate names or trigger acquisition.
    selected_skill_refs = [ref for kind, ref in bundle.selection if kind == 'skill']
    skills.update(
        ref.rsplit('/', 1)[-1]
        for ref in selected_skill_refs
        if ref.rsplit('/', 1)[-1] not in {'*', '**'}
    )
    selected_wildcard = any(ref.rsplit('/', 1)[-1] in {'*', '**'}
                            for ref in selected_skill_refs)
    def replace(match):
        skill, variable = match.groups()
        if skill is not None:
            if skill not in skills and not selected_wildcard:
                raise ConfigurationError(f"{resource.path}: unknown selected skill reference {skill}")
            return skill
        return str(values[variable]) if variable in declared else match.group(0)
    return PLACEHOLDER.sub(replace, body).strip()


def context_contributions(bundle, consumer, invocation):
    """Prepare a complete snapshot; rendering/publication belongs to sync."""
    result = []
    for resource in bundle.contexts:
        values, origins = context_values(resource, consumer, bundle)
        for destination, index, entry in attachments(resource.data):
            location = f"{resource.path}#attach.{destination}/{index}"
            if evaluate(entry.get('when'), values=values, bundle=bundle, invocation=invocation, location=location):
                identity = entry.get('id') or str(index)
                if entry.get('id') is not None and not ATTACHMENT_ID.fullmatch(identity):
                    raise ConfigurationError(f"{location}: invalid attachment id {identity!r}")
                marker = f"{resource.ref}/{destination}/{identity}"
                if marker == 'pspec' or any(character.isspace() for character in marker):
                    raise ConfigurationError(f"{location}: invalid generated identifier")
                result.append(Contribution(
                    resource, destination, _compile_body(entry['body'], resource, values, bundle),
                    MappingProxyType(values), MappingProxyType(origins), marker,
                ))
    identifiers = [item.identifier for item in result]
    if len(set(identifiers)) != len(identifiers):
        raise ConfigurationError("duplicate generated context contribution identifier")
    return tuple(result)


def trait_contributions(bundle, consumer, invocation, *, matching_refs, change=None,
                        isolate_probe_failures=False, diagnostics=None):
    """Evaluate selected traits already event-matched by the delivery caller.

    Native callback mapping and output delivery belong to the hook adapter.
    Authored condition errors remain atomic. Advisory hook callers may isolate
    operational command-probe failures to the resource that owns them.
    """
    matching = set(matching_refs)
    values, origins = runtime_values(consumer, bundle, change=change)
    result = []
    for resource in bundle.traits:
        if resource.ref not in matching:
            continue
        try:
            included = evaluate(resource.data.get('when'), values=values,
                                bundle=bundle, invocation=invocation,
                                location=f"{resource.path}#when")
        except OperationalConditionError as error:
            if not isolate_probe_failures:
                raise
            if diagnostics is not None:
                diagnostics.append(str(error))
            continue
        if included:
            result.append(Contribution(resource, None,
                                       _compile_body(resource.data['body'], resource, values, bundle),
                                       MappingProxyType(values), MappingProxyType(origins)))
    return tuple(result)

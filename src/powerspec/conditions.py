"""Evaluate trusted guidance conditions; this is not an execution sandbox."""
import os
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from collections.abc import Mapping
from zuu.case18 import RestrictedExecutor
from .catalog import ConfigurationError, Resource, attachments
from .consumer import find_git_root, runtime_values, context_values
from .utils.processes import run_json_object


class Invocation:
    def __init__(self, cwd, *, env=None, probe=None):
        self.cwd = Path(cwd).resolve(strict=True)
        self.env = dict(os.environ if env is None else env)
        self.git_root = find_git_root(self.cwd)
        self.probe = run_json_object if probe is None else probe

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
        return self.probe(argv, cwd=self.cwd, env=dict(self.env), timeout=5)


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
    except Exception as error:
        raise ConfigurationError(f"{location}: {error}") from error


@dataclass(frozen=True)
class Contribution:
    resource: Resource
    destination: str | None
    body: str
    values: Mapping
    origins: Mapping


def context_contributions(bundle, consumer, invocation):
    """Prepare a complete snapshot; rendering/publication belongs to sync."""
    result = []
    for resource in bundle.contexts:
        values, origins = context_values(resource, consumer, bundle)
        for destination, index, entry in attachments(resource.data):
            location = f"{resource.path}#attach.{destination}/{index}"
            if evaluate(entry.get('when'), values=values, bundle=bundle, invocation=invocation, location=location):
                result.append(Contribution(resource, destination, entry['body'],
                                           MappingProxyType(values), MappingProxyType(origins)))
    return tuple(result)


def trait_contributions(bundle, consumer, invocation, *, matching_refs, change=None):
    """Evaluate selected traits already event-matched by the delivery caller.

    Native callback mapping and output delivery belong to the hook adapter.
    No successful partial tuple is returned if an eligible condition fails.
    """
    matching = set(matching_refs)
    values, origins = runtime_values(consumer, bundle, change=change)
    result = []
    for resource in bundle.traits:
        if resource.ref in matching and evaluate(resource.data.get('when'), values=values,
                bundle=bundle, invocation=invocation, location=f"{resource.path}#when"):
            result.append(Contribution(resource, None, resource.data['body'],
                                       MappingProxyType(values), MappingProxyType(origins)))
    return tuple(result)

"""Compile and atomically reconcile context guidance into OpenSpec YAML."""
from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import LiteralScalarString

from .catalog import ConfigurationError
from .utils.atomic import AtomicWriteError, replace_bytes


START = "<!-- pspec:contexts:start -->"
END = "<!-- pspec:contexts:end -->"
ENTRY = "<!-- pspec:managed -->"


@dataclass(frozen=True)
class SyncResult:
    path: Path
    updated: bool


def _yaml():
    result = YAML(typ="rt")
    result.preserve_quotes = True
    result.width = 4096
    result.indent(mapping=2, sequence=4, offset=2)
    return result


def _managed_context(existing):
    if existing is None:
        return ""
    if not isinstance(existing, str):
        raise ConfigurationError("config.yaml context must be a scalar string")
    starts, ends = existing.count(START), existing.count(END)
    if starts != ends or starts > 1:
        raise ConfigurationError("config.yaml contains malformed Powerspec context markers")
    if starts == 0:
        return existing.rstrip()
    before, rest = existing.split(START, 1)
    if END not in rest:
        raise ConfigurationError("config.yaml contains malformed Powerspec context markers")
    _, after = rest.split(END, 1)
    return (before.rstrip() + ("\n" if before.strip() and after.strip() else "") + after.lstrip()).rstrip()


def _entry(value, identifier):
    return LiteralScalarString(f"{value.rstrip()}\n\n{ENTRY}\n^{identifier}\n")


def _is_managed(value):
    if not isinstance(value, str) or ENTRY not in value:
        return False
    lines = value.rstrip().splitlines()
    if len(lines) < 2 or lines[-2] != ENTRY or not lines[-1].startswith("^@"):
        raise ConfigurationError("config.yaml contains a malformed Powerspec managed entry")
    if value.count(ENTRY) != 1 or any(character.isspace() for character in lines[-1]):
        raise ConfigurationError("config.yaml contains a malformed Powerspec managed entry")
    return True


def _mapping(parent, key, location):
    value = parent.get(key)
    if value is None:
        value = CommentedMap()
        parent[key] = value
    if not isinstance(value, CommentedMap):
        raise ConfigurationError(f"config.yaml {location} must be a mapping")
    return value


def _sequence(parent, key, location):
    value = parent.get(key)
    if value is None:
        value = CommentedSeq()
        parent[key] = value
    if not isinstance(value, CommentedSeq):
        raise ConfigurationError(f"config.yaml {location} must be a list")
    return value


def reconcile(original: bytes, contributions) -> bytes:
    yaml = _yaml()
    try:
        document = yaml.load(original.decode("utf-8-sig"))
    except Exception as error:
        raise ConfigurationError(f"invalid config.yaml: {error}") from error
    if not isinstance(document, CommentedMap):
        raise ConfigurationError("config.yaml root must be a mapping")

    contributions = tuple(contributions)
    decoded = original.decode("utf-8-sig")
    untouched = not contributions and START not in decoded and END not in decoded and ENTRY not in decoded

    by_destination = {}
    for item in contributions:
        by_destination.setdefault(item.destination, []).append(item)

    user_context = _managed_context(document.get("context"))
    generated = by_destination.pop("context", [])
    if generated:
        region = [START]
        for item in generated:
            region.extend([item.body.rstrip(), f"^{item.identifier}", ""])
        region.append(END)
        combined = "\n\n".join(part for part in (user_context, "\n".join(region).rstrip()) if part)
        document["context"] = LiteralScalarString(combined.rstrip() + "\n")
    elif START in str(document.get("context", "")):
        if user_context:
            document["context"] = LiteralScalarString(user_context.rstrip() + "\n")
        else:
            del document["context"]

    # Remove every prior managed list entry before appending the complete snapshot.
    for top in ("rules", "operations"):
        container = document.get(top)
        if container is not None and not isinstance(container, CommentedMap):
            raise ConfigurationError(f"config.yaml {top} must be a mapping")
    rules = document.get("rules")
    if isinstance(rules, CommentedMap):
        for name, values in rules.items():
            if not isinstance(values, CommentedSeq):
                raise ConfigurationError(f"config.yaml rules.{name} must be a list")
            values[:] = [value for value in values if not _is_managed(value)]
    operations = document.get("operations")
    if isinstance(operations, CommentedMap):
        for name, operation in operations.items():
            if not isinstance(operation, CommentedMap):
                raise ConfigurationError(f"config.yaml operations.{name} must be a mapping")
            guidance = operation.get("guidance")
            if guidance is not None:
                if not isinstance(guidance, CommentedSeq):
                    raise ConfigurationError(f"config.yaml operations.{name}.guidance must be a list")
                guidance[:] = [value for value in guidance if not _is_managed(value)]

    if untouched:
        return original

    for destination, items in by_destination.items():
        parts = destination.split(".")
        if len(parts) == 2 and parts[0] == "rules":
            values = _sequence(_mapping(document, "rules", "rules"), parts[1], destination)
        elif len(parts) == 3 and parts[0] == "operations" and parts[2] == "guidance":
            operation = _mapping(_mapping(document, "operations", "operations"), parts[1], ".".join(parts[:2]))
            values = _sequence(operation, "guidance", destination)
        else:
            raise ConfigurationError(f"unsupported context destination: {destination}")
        values.extend(_entry(item.body, item.identifier) for item in items)

    stream = StringIO()
    yaml.dump(document, stream)
    candidate = stream.getvalue().encode("utf-8")
    # Round-trip parsability is part of complete validation.
    try:
        _yaml().load(candidate.decode("utf-8"))
    except Exception as error:
        raise ConfigurationError(f"rendered config.yaml is invalid: {error}") from error
    return original if candidate == original else candidate


def publish(path: Path, contributions) -> SyncResult:
    path = Path(path).resolve(strict=True)
    if not path.is_file():
        raise ConfigurationError(f"{path}: target config.yaml is not a file")
    try:
        original = path.read_bytes()
        candidate = reconcile(original, contributions)
    except OSError as error:
        raise ConfigurationError(f"{path}: {error}") from error
    try:
        updated = replace_bytes(path, candidate)
    except AtomicWriteError as error:
        raise ConfigurationError(f"{path}: publication failed: {error}") from error
    return SyncResult(path, updated)

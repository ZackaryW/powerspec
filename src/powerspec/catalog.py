"""Validated, read-only catalog inputs; no acquisition or native installation."""
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Mapping
import ast
import re
import tomllib
import yaml


class ConfigurationError(ValueError):
    """A resource or consumer contract was violated."""


KINDS = {"profile", "context", "trait", "skill"}
NAME = re.compile(r"[a-z0-9][a-z0-9-]*")


def reference(value: str, *, wildcard: bool = False) -> str:
    if not isinstance(value, str) or not value.startswith("@") or "\\" in value:
        raise ConfigurationError(f"expected qualified resource reference: {value!r}")
    parts = value[1:].split("/")
    if len(parts) < 2 or any(not part or part in {".", ".."} for part in parts):
        raise ConfigurationError(f"malformed resource reference: {value!r}")
    if not NAME.fullmatch(parts[0]) or any(any(c.isspace() for c in p) for p in parts):
        raise ConfigurationError(f"malformed resource reference: {value!r}")
    if parts[0] == "gitsource":
        if len(parts) < 3 or parts[1] == "builtin":
            raise ConfigurationError(f"invalid or reserved Git source: {value}")
    elif len(parts) != 2 or not NAME.fullmatch(parts[1]):
        raise ConfigurationError(f"invalid resource name: {value}")
    for part in parts:
        if any(c in part for c in "*?[]") and not (wildcard and part in {"*", "**"}):
            raise ConfigurationError(f"wildcard is not an exact reference: {value}")
        if ":" in part or "\x00" in part:
            raise ConfigurationError(f"invalid reference segment: {value!r}")
    return value


def read_toml(path: Path) -> dict:
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except (OSError, ValueError) as error:
        raise ConfigurationError(f"{path}: {error}") from error


def expression(value: object, location: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{location}: when must be a Python expression string; migrate check maps")
    try:
        ast.parse(value, filename=location, mode="eval")
    except SyntaxError as error:
        raise ConfigurationError(f"{location}: invalid condition: {error.msg}") from error


def _strings(data, key, *, qualified=False):
    value = data.get(key, [])
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
        raise ConfigurationError(f"{key} must be a list of strings")
    if qualified:
        for item in value:
            reference(item, wildcard=key == "skills")
    return value


def attachments(data: Mapping):
    """Yield destination, ordinal, entry without executing conditions."""
    def walk(node, path):
        if isinstance(node, list):
            destination = ".".join(path)
            valid = (path == ("context",) or len(path) == 2 and path[0] == "rules"
                     or len(path) == 3 and path[0] == "operations" and path[2] == "guidance")
            if not valid:
                raise ConfigurationError(f"unsupported attachment destination: {destination}")
            for index, item in enumerate(node, 1):
                if not isinstance(item, dict) or not isinstance(item.get("body"), str):
                    raise ConfigurationError(f"{destination}/{index}: expected body string")
                if set(item) - {"body", "when", "id"}:
                    raise ConfigurationError(f"{destination}/{index}: unknown attachment fields")
                if "when" in item:
                    expression(item["when"], f"{destination}/{index}")
                yield destination, index, item
        elif isinstance(node, Mapping):
            for key, value in node.items():
                yield from walk(value, path + (key,))
        else:
            raise ConfigurationError("attach must contain destination tables and entry arrays")
    yield from walk(data.get("attach", {}), ())


def validate(kind: str, data: dict) -> None:
    if "mode" in data or "check" in data:
        raise ConfigurationError("migrate legacy mode/check fields: contexts use attach; traits use hooks/body and Python when")
    if kind == "profile":
        allowed = {"scope", "global", "profiles", "contexts", "traits", "skills", "vars", "exclude-profiles"}
        if set(data) - allowed:
            raise ConfigurationError("profiles own references/defaults, not destinations or selectors")
        if data.get("scope", "user") not in {"user", "project"}:
            raise ConfigurationError("scope must be user or project")
        if type(data.get("global", False)) is not bool or not isinstance(data.get("vars", {}), dict):
            raise ConfigurationError("global must be Boolean and vars a table")
        for field in ("profiles", "contexts", "traits", "skills", "exclude-profiles"):
            _strings(data, field, qualified=True)
    elif kind == "trait":
        if set(data) - {"hooks", "body", "when"}:
            raise ConfigurationError("runtime traits use hooks/body; move compile-time guidance to contexts")
        if not _strings(data, "hooks") or not isinstance(data.get("body"), str):
            raise ConfigurationError("trait requires hooks and body")
        if "when" in data:
            expression(data["when"], "when")
    elif kind == "context":
        if set(data) - {"attach", "compiletime"}:
            raise ConfigurationError("contexts use attach/compiletime, not runtime hooks/body/when")
        list(attachments(data))
        declarations = data.get("compiletime", [])
        if not isinstance(declarations, list):
            raise ConfigurationError("compiletime must be an array of declarations")
        seen = set()
        for item in declarations:
            if not isinstance(item, dict) or set(item) - {"id", "type", "default", "choices"}:
                raise ConfigurationError("compiletime declarations support id/type/choices/default, never prompt parsers")
            key = item.get("id")
            if not isinstance(key, str) or not key or key in seen:
                raise ConfigurationError("compiletime ids must be unique nonempty strings")
            seen.add(key)
            if item.get("type") not in {"string", "boolean", "integer", "float"}:
                raise ConfigurationError(f"{key}: unsupported compiletime type")
            if "choices" in item and (not isinstance(item["choices"], list) or not item["choices"]):
                raise ConfigurationError(f"{key}: choices must be a nonempty list")


@dataclass(frozen=True)
class Resource:
    kind: str
    ref: str
    name: str
    path: Path
    data: dict


class Catalog:
    """Inject builtin explicitly; sources and gitsources are already materialized.

    Consumer resources can be registered as a private 'local' source by the
    consumer caller. No arbitrary repository is discovered or called builtin.
    """
    def __init__(self, *, builtin: Path | None = None, sources=None, gitsources=None):
        self.resources: dict[tuple[str, str], Resource] = {}
        sources, gitsources = dict(sources or {}), dict(gitsources or {})
        if "builtin" in sources or "builtin" in gitsources or "gitsource" in sources:
            raise ConfigurationError("builtin and gitsource are reserved source namespaces")
        if builtin is not None:
            self._catalog("builtin", Path(builtin))
        for source, root in sources.items():
            if not isinstance(source, str) or not NAME.fullmatch(source):
                raise ConfigurationError(f"invalid source identity: {source!r}")
            self._catalog(source, Path(root))
        for source, root in gitsources.items():
            if not isinstance(source, str) or not NAME.fullmatch(source):
                raise ConfigurationError(f"invalid Git source identity: {source!r}")
            root = Path(root).resolve(strict=True)
            names = set()
            for path in sorted(root.rglob("SKILL.md")):
                name, data = self._skill(path, root)
                if name in names:
                    raise ConfigurationError(f"{path}: duplicate skill name {name} in {source}")
                names.add(name)
                ref = f"@gitsource/{source}/{path.parent.relative_to(root).as_posix()}"
                self._add(Resource("skill", reference(ref), name, path.resolve(), data))

    @staticmethod
    def _contained(path, root):
        if not path.resolve().is_relative_to(root):
            raise ConfigurationError(f"{path}: resource escapes source root")

    def _add(self, resource):
        key = resource.kind, resource.ref
        if key in self.resources:
            raise ConfigurationError(f"{resource.path}: duplicate {resource.kind} identity {resource.ref}")
        self.resources[key] = resource

    def _skill(self, path, root):
        self._contained(path, root)
        try:
            text = path.read_text(encoding="utf-8-sig")
            lines = text.splitlines()
            if not lines or lines[0] != "---":
                raise ValueError("missing skill frontmatter")
            end = lines.index("---", 1)
            data = yaml.safe_load("\n".join(lines[1:end]))
            name = data.get("name") if isinstance(data, dict) else None
            if not isinstance(name, str) or not NAME.fullmatch(name):
                raise ValueError("skill name must contain lowercase letters, numbers, and hyphens")
            return name, data
        except (OSError, ValueError, yaml.YAMLError) as error:
            raise ConfigurationError(f"{path}: {error}") from error

    def _catalog(self, source, root):
        root = root.resolve(strict=True)
        for kind in ("profile", "context", "trait"):
            for path in sorted((root / (kind + "s")).glob("*.toml")):
                self._contained(path, root)
                try:
                    data = read_toml(path)
                    validate(kind, data)
                    ref = reference(f"@{source}/{path.stem}")
                except ConfigurationError as error:
                    raise ConfigurationError(f"{path}: {error}") from error
                self._add(Resource(kind, ref, path.stem, path.resolve(), data))
        for path in sorted((root / "skills").glob("*/SKILL.md")):
            name, data = self._skill(path, root)
            self._add(Resource("skill", f"@{source}/{name}", name, path.resolve(), data))

    def get(self, kind, ref):
        if kind not in KINDS:
            raise ConfigurationError(f"unknown resource kind: {kind}")
        reference(ref)
        try:
            return self.resources[kind, ref]
        except KeyError:
            raise ConfigurationError(f"missing {kind}: {ref}") from None

    def select(self, kind, ref):
        reference(ref, wildcard=kind == "skill")
        if "*" not in ref:
            return (self.get(kind, ref),)
        prefix, pattern = ref.rsplit("/", 1)
        if pattern not in {"*", "**"} or not ref.startswith("@gitsource/") or "*" in prefix:
            raise ConfigurationError(f"unsupported selector: {ref}")
        matched = tuple(r for (k, identity), r in self.resources.items()
                        if k == kind and identity.startswith(prefix + "/")
                        and (pattern == "**" or "/" not in identity[len(prefix)+1:]))
        if not matched:
            raise ConfigurationError(f"no materialized resources for selector: {ref}")
        return matched

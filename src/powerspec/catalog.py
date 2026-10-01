"""Validated, read-only catalog inputs; no acquisition or native installation."""
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Mapping
import re
import tomllib
import yaml
from pydantic import ValidationError
from .models import Profile, Context, Trait


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
        if len(parts) < 3 or not NAME.fullmatch(parts[1]) or parts[1] == "builtin":
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


def attachments(data: Mapping):
    """Yield destination, ordinal, entry from an already validated context."""
    attach = data.get("attach", {})
    for index, item in enumerate(attach.get("context", []), 1):
        yield "context", index, item
    for name, entries in attach.get("rules", {}).items():
        for index, item in enumerate(entries, 1):
            yield f"rules.{name}", index, item
    for name, operation in attach.get("operations", {}).items():
        for index, item in enumerate(operation.get("guidance", []), 1):
            yield f"operations.{name}.guidance", index, item


def validate(kind: str, data: dict) -> None:
    if "mode" in data or "check" in data:
        raise ConfigurationError("migrate legacy mode/check fields: contexts use attach; traits use hooks/body and Python when")
    model = {"profile": Profile, "context": Context, "trait": Trait}.get(kind)
    if model is None:
        raise ConfigurationError(f"unsupported configuration kind: {kind}")
    try:
        parsed = model.model_validate(data)
    except ValidationError as error:
        raise ConfigurationError(str(error)) from error
    if isinstance(parsed, Profile):
        for field in ("profiles", "contexts", "traits", "skills", "exclude_profiles"):
            for item in getattr(parsed, field):
                reference(item, wildcard=field == "skills")


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

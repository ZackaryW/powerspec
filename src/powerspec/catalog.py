"""Validated, read-only catalog inputs; no acquisition or native installation."""
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from collections.abc import Mapping, Sequence
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
        wildcard_parts = [index for index, part in enumerate(parts) if part in {"*", "**"}]
        if wildcard_parts and (not wildcard or wildcard_parts != [len(parts) - 1]):
            raise ConfigurationError(f"Git source wildcard must be the final selector segment: {value}")
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
    provenance: Mapping | None = None


class Catalog:
    """Inject builtin explicitly; sources and gitsources are already materialized.

    Consumer resources can be registered as a private 'local' source by the
    consumer caller. No arbitrary repository is discovered or called builtin.
    """
    def __init__(self, *, builtin: Path | None = None, sources=None, gitsources=None,
                 git_resolver=None):
        self.resources: dict[tuple[str, str], Resource] = {}
        self.gitsources = {}
        self.git_recipes = {}
        self._fixed_gitsources = set()
        self.git_resolver = git_resolver
        sources, gitsources = dict(sources or {}), dict(gitsources or {})
        if "builtin" in sources or "builtin" in gitsources or "gitsource" in sources:
            raise ConfigurationError("builtin and gitsource are reserved source namespaces")
        if builtin is not None:
            self._catalog("builtin", Path(builtin))
        for source, root in sources.items():
            if not isinstance(source, str) or not NAME.fullmatch(source):
                raise ConfigurationError(f"invalid source identity: {source!r}")
            roots = root if isinstance(root, Sequence) and not isinstance(root, (str, bytes, Path)) else (root,)
            for item in roots:
                self._catalog(source, Path(item))
        for source, materialization in gitsources.items():
            self._git_source(source, materialization)
            self._fixed_gitsources.add(source)

    def set_git_recipes(self, recipes):
        """Replace profile-owned recipes used for lazy Git materialization."""
        selected = {}
        for source, recipe in dict(recipes).items():
            if not isinstance(source, str) or not NAME.fullmatch(source) or source == "builtin":
                raise ConfigurationError(f"invalid or reserved Git source identity: {source!r}")
            selected[source] = dict(recipe)
        self.git_recipes = selected
        for source in tuple(self.gitsources):
            if source not in self._fixed_gitsources:
                del self.gitsources[source]

    def _git_source(self, source, materialization):
        if not isinstance(source, str) or not NAME.fullmatch(source):
            raise ConfigurationError(f"invalid Git source identity: {source!r}")
        candidate = materialization if isinstance(materialization, (str, bytes, PathLike)) else materialization.root
        root = Path(candidate).resolve(strict=True)
        if not root.is_dir():
            raise ConfigurationError(f"Git source {source!r} is not a directory: {root}")
        identity = getattr(materialization, "identity", source)
        if identity != source:
            raise ConfigurationError(f"Git source key {source!r} does not match binding {identity!r}")
        self.gitsources[source] = (root, materialization)

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
        if kind == "skill" and ref.startswith("@gitsource/"):
            return self._select_git(ref)[0]
        try:
            return self.resources[kind, ref]
        except KeyError:
            raise ConfigurationError(f"missing {kind}: {ref}") from None

    def select(self, kind, ref, *, allow_empty=False):
        reference(ref, wildcard=kind == "skill")
        if kind == "skill" and ref.startswith("@gitsource/"):
            return self._select_git(ref, allow_empty=allow_empty)
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

    def _select_git(self, ref, *, allow_empty=False):
        parts = ref[1:].split("/")
        source, selector = parts[1], parts[2:]
        try:
            root, materialization = self.gitsources[source]
        except KeyError:
            try:
                recipe = self.git_recipes[source]
            except KeyError:
                raise ConfigurationError(f"missing source declaration for Git source alias: {source}") from None
            if self.git_resolver is None:
                raise ConfigurationError(f"Git source alias is not materialized: {source}") from None
            self._git_source(source, self.git_resolver(source, dict(recipe)))
            root, materialization = self.gitsources[source]
        pattern = selector[-1] if selector else None
        prefix = root.joinpath(*selector[:-1]) if pattern in {"*", "**"} else root.joinpath(*selector)
        try:
            resolved_prefix = prefix.resolve(strict=True)
        except OSError as error:
            raise ConfigurationError(f"{ref}: selected path does not exist: {prefix}") from error
        self._contained(resolved_prefix, root)
        if not resolved_prefix.is_dir():
            raise ConfigurationError(f"{ref}: selected path is not a directory")
        if pattern == "*":
            entries = [path / "SKILL.md" for path in sorted(resolved_prefix.iterdir()) if path.is_dir()]
        elif pattern == "**":
            entries = sorted(resolved_prefix.rglob("SKILL.md"))
        else:
            entries = [resolved_prefix / "SKILL.md"]
        entries = [path for path in entries if path.is_file()]
        if not entries:
            if allow_empty:
                return ()
            raise ConfigurationError(f"no materialized resources for selector: {ref}")
        resources, names = [], {}
        for entry in entries:
            self._contained(entry, root)
            name, data = self._skill(entry, root)
            relative = entry.parent.resolve().relative_to(root).as_posix()
            if name in names:
                raise ConfigurationError(
                    f"{entry}: duplicate selected skill name {name}; already declared by {names[name]}"
                )
            names[name] = entry
            identity = reference(f"@gitsource/{source}/{relative}")
            provenance = {
                "provider": "git",
                "source": source,
                "path": relative,
            }
            for key, attribute in (
                ("repository", "repository"),
                ("requested_revision", "requested_revision"),
                ("resolved_revision", "resolved_revision"),
                ("source_id", "source_id"),
                ("artifact_id", "artifact_id"),
            ):
                value = getattr(materialization, attribute, None)
                if value is not None:
                    provenance[key] = value
            resources.append(Resource("skill", identity, name, entry.resolve(), data, provenance))
        return tuple(resources)

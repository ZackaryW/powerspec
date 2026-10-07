"""Verified Saucepan source lookup and explicit Git acquisition."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
import os
from pathlib import Path
import re
from typing import Literal
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from saucepan_sdk import Saucepan, SaucepanError

from .catalog import ConfigurationError, MetadataUnavailable, NAME
from .saucepan_tool import ensure_saucepan_binary, inspect_saucepan_binary, inspection_remaining


class _WireModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore")


class _GitSource(_WireModel):
    provider: Literal["git"]
    origin: str = Field(min_length=1)
    reference: str = Field(min_length=1)


class _Artifact(_WireModel):
    id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source: _GitSource
    snapshot_id: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    folder: str | None


class _View(_WireModel):
    version: Literal[1]
    app: str
    entries: dict[str, _Artifact]


class _Snapshot(_WireModel):
    id: str = Field(min_length=1)
    revision: str = Field(min_length=1)


class _History(_WireModel):
    source: _GitSource
    current: _Snapshot | None


class _Acquired(_WireModel):
    artifact: _Artifact
    directory: str = Field(min_length=1)
    content_verified: bool


@dataclass(frozen=True)
class SourceBinding:
    """One validated, full-repository Saucepan materialization."""

    identity: str
    repository: str
    requested_revision: str
    resolved_revision: str
    source_id: str
    artifact_id: str
    root: Path


class SaucepanSources:
    """Resolve profile-owned recipes through one shared Powerspec application."""

    APP = "powerspec"

    def __init__(self, client: Saucepan | None = None, *, manage_binary: bool = True):
        self._client = client
        self._manage_binary = manage_binary

    def _client_or_default(self, *, deadline=None):
        if self._client is None:
            binary = (
                ensure_saucepan_binary()
                if self._manage_binary and deadline is None
                else inspect_saucepan_binary(**({} if deadline is None else {'deadline': deadline}))
            )
            self._client = Saucepan(binary=binary)
        return self._client

    def _read(self, app, method, *args, deadline=None):
        if deadline is not None:
            # Construct through the public SDK API for each remaining allowance.
            app = Saucepan(binary=self._client.binary,
                           timeout=inspection_remaining(deadline)).for_app(self.APP)
        return getattr(app, method)(*args)

    @staticmethod
    def _identity(identity: str) -> str:
        if not isinstance(identity, str) or not NAME.fullmatch(identity) or identity == "builtin":
            raise ConfigurationError(f"invalid or reserved Git source identity: {identity!r}")
        return identity

    @staticmethod
    def _source(identity: str, recipe) -> _GitSource:
        SaucepanSources._identity(identity)
        try:
            # Profile composition freezes authored mappings before exposing the
            # effective bundle. Pydantic's strict model validator accepts a
            # concrete mapping but rejects MappingProxyType, so normalize any
            # mapping-shaped recipe at this wire boundary.
            payload = dict(recipe) if isinstance(recipe, Mapping) else recipe
            return _GitSource.model_validate(payload)
        except ValidationError as error:
            raise ConfigurationError(f"invalid Git source recipe for {identity!r}: {error}") from error

    @staticmethod
    def _missing(error, message: str) -> bool:
        if not isinstance(error, SaucepanError):
            return False
        diagnostic = f"{getattr(error, 'stderr', '')} {error}".lower()
        return message in diagnostic

    @staticmethod
    def _origin_path(origin: str) -> str | None:
        parsed = urlparse(origin)
        if re.match(r"^[A-Za-z]:[\\/]", origin) or origin.startswith("\\\\"):
            path = origin
        elif parsed.scheme == "file":
            path = url2pathname(unquote(parsed.path))
            if parsed.netloc:
                path = f"//{parsed.netloc}{path}"
        elif parsed.scheme or not Path(origin).is_absolute():
            return None
        else:
            path = origin
        try:
            return os.path.normcase(str(Path(path).resolve(strict=False)))
        except (OSError, ValueError):
            return None

    @staticmethod
    def _remote_origin(origin: str):
        parsed = urlparse(origin)
        if parsed.scheme.lower() not in {"git", "http", "https", "ssh"} or not parsed.netloc:
            return None
        path = parsed.path.rstrip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.params, parsed.query, parsed.fragment

    @classmethod
    def _same_source(cls, left: _GitSource, right: _GitSource) -> bool:
        if left.provider != right.provider or left.reference != right.reference:
            return False
        if left.origin == right.origin:
            return True
        left_path, right_path = cls._origin_path(left.origin), cls._origin_path(right.origin)
        if left_path is not None or right_path is not None:
            return left_path is not None and right_path is not None and left_path == right_path
        left_remote, right_remote = cls._remote_origin(left.origin), cls._remote_origin(right.origin)
        return left_remote is not None and right_remote is not None and left_remote == right_remote

    def _application(self, *, create: bool, deadline=None):
        client = self._client_or_default(deadline=deadline)
        app = client.for_app(self.APP)
        try:
            view = _View.model_validate(self._read(app, 'view', deadline=deadline))
        except (SaucepanError, ValidationError, OSError, ValueError) as error:
            if not create:
                raise MetadataUnavailable(f"Powerspec Saucepan application is unavailable: {error}") from error
            if any(self._missing(error, message) for message in (
                "store index is missing", "store secret is missing",
            )):
                try:
                    # Native stores check the OS secret before the index. Let
                    # Saucepan distinguish first use from damaged existing data;
                    # never replace its secret or delete its store ourselves.
                    client.init()
                except (SaucepanError, OSError, ValueError) as init_error:
                    raise ConfigurationError(f"cannot initialize Saucepan store: {init_error}") from init_error
            elif not self._missing(error, "app is not registered"):
                raise ConfigurationError(f"Powerspec Saucepan application is unavailable: {error}") from error
            try:
                client.register(self.APP)
            except (SaucepanError, OSError, ValueError) as register_error:
                if not self._missing(register_error, "app is already registered"):
                    raise ConfigurationError(
                        f"cannot register Powerspec Saucepan application: {register_error}"
                    ) from register_error
            try:
                view = _View.model_validate(app.view())
            except (SaucepanError, ValidationError, OSError, ValueError) as view_error:
                raise ConfigurationError(
                    f"Powerspec Saucepan application is unavailable after registration: {view_error}"
                ) from view_error
        if view.app != self.APP:
            raise ConfigurationError(
                f"Saucepan returned application {view.app!r}; expected {self.APP!r}"
            )
        return app, view

    def _binding(self, identity: str, source: _GitSource, app, view: _View, *, deadline=None) -> SourceBinding:
        matched = [item for item in view.entries.values() if self._same_source(item.source, source)]
        source_ids = {item.source_id for item in matched}
        if not source_ids:
            raise MetadataUnavailable(f"Git source {identity!r} has no current materialization in Saucepan")
        if len(source_ids) != 1:
            raise ConfigurationError(
                f"Git source {identity!r} is ambiguous in Saucepan: found {len(source_ids)} matching sources"
            )
        source_id = next(iter(source_ids))
        try:
            history = _History.model_validate(self._read(app, 'history', source_id, deadline=deadline))
        except (SaucepanError, ValidationError, OSError, ValueError) as error:
            raise MetadataUnavailable(f"cannot inspect Saucepan source {identity!r}: {error}") from error
        if not self._same_source(history.source, source):
            raise ConfigurationError(f"Saucepan history does not match declared recipe for {identity!r}")
        if history.current is None:
            raise MetadataUnavailable(f"Saucepan source {identity!r} has no current materialization")
        candidates = [item for item in matched
                      if item.snapshot_id == history.current.id and item.folder is None]
        if len(candidates) != 1:
            raise MetadataUnavailable(
                f"Saucepan source {identity!r} has no unique full-repository current artifact"
            )
        artifact = candidates[0]
        try:
            located = self._read(app, 'path', artifact.id, deadline=deadline)
        except (SaucepanError, OSError, ValueError) as error:
            raise MetadataUnavailable(f"cannot locate Saucepan source {identity!r}: {error}") from error
        if not located:
            raise MetadataUnavailable(f"Saucepan source {identity!r} materialization is missing")
        try:
            root = Path(located).resolve(strict=True)
        except OSError as error:
            raise MetadataUnavailable(f"Saucepan source {identity!r} materialization is unavailable: {error}") from error
        if not root.is_dir():
            raise ConfigurationError(f"Saucepan source {identity!r} is not a directory: {root}")
        return SourceBinding(identity, source.origin, source.reference, artifact.revision,
                             source_id, artifact.id, root)

    def lookup(self, identity: str, recipe, *, deadline=None) -> SourceBinding:
        """Return the current complete materialization without fetching or repair."""
        source = self._source(identity, recipe)
        app, view = self._application(create=False, deadline=deadline)
        return self._binding(identity, source, app, view, deadline=deadline)

    def _acquire(self, identity: str, source: _GitSource, app) -> SourceBinding:
        try:
            result = _Acquired.model_validate(app.acquire({"source": source.model_dump()}))
        except (SaucepanError, ValidationError, OSError, ValueError) as error:
            raise ConfigurationError(f"failed to acquire Saucepan source {identity!r}: {error}") from error
        artifact = result.artifact
        matches = self._same_source(artifact.source, source)
        if not matches or artifact.folder is not None:
            raise ConfigurationError(
                f"Saucepan returned an invalid full-repository binding for {identity!r}: "
                f"recipe_match={matches!r}, folder={artifact.folder!r}"
            )
        root = Path(result.directory).resolve(strict=True)
        if not root.is_dir():
            raise ConfigurationError(f"Saucepan source {identity!r} is not a directory: {root}")
        return SourceBinding(identity, source.origin, source.reference, artifact.revision,
                             artifact.source_id, artifact.id, root)

    def acquire(self, identity: str, recipe) -> SourceBinding:
        """Refresh a declared recipe in the existing Powerspec application."""
        source = self._source(identity, recipe)
        app, _view = self._application(create=False)
        return self._acquire(identity, source, app)

    def ensure(self, identity: str, recipe) -> SourceBinding:
        """Create the Powerspec app if needed and acquire only a missing recipe."""
        source = self._source(identity, recipe)
        app, view = self._application(create=True)
        if any(self._same_source(item.source, source) for item in view.entries.values()):
            return self._binding(identity, source, app, view)
        return self._acquire(identity, source, app)


def discover_catalogs(root: Path) -> tuple[Path, ...]:
    """Find reusable catalogs while excluding private OpenSpec consumers."""
    source = Path(root).resolve(strict=True)
    if not source.is_dir():
        raise ConfigurationError(f"source materialization is not a directory: {source}")
    candidates = ([source] if source.name == ".pspec" else []) + list(source.rglob(".pspec"))
    found = []
    for candidate in sorted(candidates):
        if not candidate.is_dir() or candidate.parent.name.lower() == "openspec":
            continue
        resolved = candidate.resolve(strict=True)
        if not resolved.is_relative_to(source):
            raise ConfigurationError(f"{candidate}: reusable catalog escapes source root")
        if resolved not in found:
            found.append(resolved)
    if not found:
        raise ConfigurationError(f"{source}: no reusable .pspec catalog")
    return tuple(found)


@dataclass(frozen=True)
class CatalogBinding:
    source: SourceBinding
    catalogs: tuple[Path, ...]


class ExternalCatalogs:
    """Validated external catalog bindings; failed replacements are atomic."""

    def __init__(self, bindings=None):
        self.bindings = dict(bindings or {})

    def register(self, binding: SourceBinding) -> "ExternalCatalogs":
        from .catalog import Catalog

        if binding.identity == "builtin":
            raise ConfigurationError("builtin is a reserved source identity")
        catalogs = discover_catalogs(binding.root)
        # Constructing the candidate validates all declarations and collisions
        # before a replacement mapping can become observable.
        Catalog(sources={binding.identity: catalogs})
        replacement = dict(self.bindings)
        replacement[binding.identity] = CatalogBinding(binding, catalogs)
        return ExternalCatalogs(replacement)

    def sources(self):
        return {identity: item.catalogs for identity, item in self.bindings.items()}

"""Verified Saucepan source lookup and explicit Git acquisition."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from saucepan_sdk import Saucepan, SaucepanError

from .catalog import ConfigurationError, NAME


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
    """Resolve registered Saucepan app identities without implicit acquisition."""

    def __init__(self, client: Saucepan | None = None):
        self._client = client or Saucepan()

    @staticmethod
    def _identity(identity: str) -> str:
        if not isinstance(identity, str) or not NAME.fullmatch(identity) or identity == "builtin":
            raise ConfigurationError(f"invalid or reserved Git source identity: {identity!r}")
        return identity

    def _registered(self, identity: str):
        identity = self._identity(identity)
        app = self._client.for_app(identity)
        try:
            view = _View.model_validate(app.view())
        except (SaucepanError, ValidationError, OSError, ValueError) as error:
            raise ConfigurationError(f"Git source {identity!r} is not available from Saucepan: {error}") from error
        sources = {item.source_id: item.source for item in view.entries.values()}
        if not sources:
            raise ConfigurationError(f"Saucepan source {identity!r} has no touched Git source")
        if len(sources) != 1:
            raise ConfigurationError(
                f"Saucepan source {identity!r} is ambiguous: expected one touched Git source, found {len(sources)}"
            )
        source_id, source = next(iter(sources.items()))
        return app, view, source_id, source

    def lookup(self, identity: str) -> SourceBinding:
        """Return the current complete materialization without fetching or repair."""
        app, view, source_id, source = self._registered(identity)
        try:
            history = _History.model_validate(app.history(source_id))
        except (SaucepanError, ValidationError, OSError, ValueError) as error:
            raise ConfigurationError(f"cannot inspect Saucepan source {identity!r}: {error}") from error
        if history.current is None:
            raise ConfigurationError(f"Saucepan source {identity!r} has no current materialization")
        candidates = [item for item in view.entries.values()
                      if item.source_id == source_id and item.snapshot_id == history.current.id
                      and item.folder is None]
        if len(candidates) != 1:
            raise ConfigurationError(
                f"Saucepan source {identity!r} has no unique full-repository current artifact"
            )
        artifact = candidates[0]
        try:
            located = app.path(artifact.id)
        except (SaucepanError, OSError, ValueError) as error:
            raise ConfigurationError(f"cannot locate Saucepan source {identity!r}: {error}") from error
        if not located:
            raise ConfigurationError(f"Saucepan source {identity!r} materialization is missing")
        root = Path(located).resolve(strict=True)
        if not root.is_dir():
            raise ConfigurationError(f"Saucepan source {identity!r} is not a directory: {root}")
        return SourceBinding(identity, source.origin, source.reference, artifact.revision,
                             source_id, artifact.id, root)

    def acquire(self, identity: str) -> SourceBinding:
        """Refresh an existing registered identity and return its complete repository."""
        app, _view, source_id, source = self._registered(identity)
        try:
            result = _Acquired.model_validate(app.acquire({"source": source.model_dump()}))
        except (SaucepanError, ValidationError, OSError, ValueError) as error:
            raise ConfigurationError(f"failed to acquire Saucepan source {identity!r}: {error}") from error
        artifact = result.artifact
        if artifact.source_id != source_id or artifact.folder is not None:
            raise ConfigurationError(
                f"Saucepan returned an invalid full-repository binding for {identity!r}: "
                f"source_id={artifact.source_id!r}, expected={source_id!r}, "
                f"folder={artifact.folder!r}"
            )
        root = Path(result.directory).resolve(strict=True)
        if not root.is_dir():
            raise ConfigurationError(f"Saucepan source {identity!r} is not a directory: {root}")
        return SourceBinding(identity, source.origin, source.reference, artifact.revision,
                             source_id, artifact.id, root)


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

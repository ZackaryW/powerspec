"""Consumer-scoped retained milkpan selections; lookup never mutates the bucket."""
from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Literal
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .catalog import ConfigurationError, MetadataUnavailable, NAME
from .milkpan_binary import MILKPAN, Release, candidate_scope, default_home, ensure_consumer_policy, ensure_milkpan, inspect_milkpan
from .milkpan_client import Milkpan, MilkpanError, MilkpanUnavailable
from .utils.atomic import replace_bytes
from .progress import stage


class _GitSource(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    provider: Literal['git']
    origin: str = Field(min_length=1)
    reference: str = Field(min_length=1)


@dataclass(frozen=True)
class SourceBinding:
    identity: str
    repository: str
    requested_revision: str
    resolved_revision: str
    source_id: str
    artifact_id: str
    root: Path


SUPPORTED_ORIGINS = 'https://github.com/<owner>/<repo>, an absolute local path, or a file:// URL'


def milkpan_spec(origin: str) -> str:
    """The milkpan spec (without selector) for a recipe origin."""
    parsed = urlparse(origin)
    if parsed.scheme.lower() == 'https' and parsed.netloc.lower() == 'github.com':
        parts = [part for part in parsed.path.strip('/').removesuffix('.git').split('/') if part]
        if len(parts) == 2 and not parsed.query and not parsed.fragment:
            return f'github:{parts[0].lower()}/{parts[1].lower()}'
    if re.match(r'^[A-Za-z]:[\\/]', origin):
        path = origin
    elif parsed.scheme.lower() == 'file':
        path = url2pathname(unquote(parsed.path))
        if parsed.netloc:
            path = f'//{parsed.netloc}{path}'
    elif not parsed.scheme and Path(origin).is_absolute():
        path = origin
    else:
        raise ConfigurationError(f'unsupported Git origin {origin!r}: milkpan supports {SUPPORTED_ORIGINS}')
    resolved = str(Path(path).resolve(strict=False)).replace('\\', '/')
    return f'local:{resolved}'


class MilkpanSources:
    """Publish selected commit leases in the owning consumer's local state.

    A recipe's reference is resolved in the consumer's candidate scope (cached
    for a day), then the exact commit is leased in the consumer's scope. That
    lease's content path never changes, and its blob is shared with every other
    lease on the same commit.
    """

    def __init__(self, client: Milkpan | None = None, *, manage_binary=True,
                 consumer_path: Path | None = None, home: Path | None = None, release: Release = MILKPAN):
        self._client = client
        self._manage_binary = manage_binary
        self._release = release
        client_home = getattr(client, 'home', None)
        self.home = Path(home) if home else (Path(client_home) if client_home else default_home())
        self.consumer_path = Path(consumer_path or Path.home() / '.powerspec/config.toml').resolve()
        self.scope = 'consumer-' + hashlib.sha256(os.path.normcase(str(self.consumer_path)).encode()).hexdigest()
        self.state_path = self.consumer_path.parent / 'milkpan-state.json'
        self._candidates = {}

    def for_consumer(self, path):
        if Path(path).resolve() == self.consumer_path:
            return self
        return MilkpanSources(self._client, manage_binary=self._manage_binary, consumer_path=path,
                              home=self.home, release=self._release)

    def _milkpan(self, *, deadline=None) -> Milkpan:
        if self._client is None:
            if self._manage_binary and deadline is None:
                with stage('Preparing milkpan'):
                    self._client = ensure_milkpan(self.home, release=self._release)
            else:
                self._client = inspect_milkpan(self.home, release=self._release)
        if deadline is not None:
            return self._client.with_timeout(_remaining(deadline))
        return self._client

    @staticmethod
    def _source(identity, recipe):
        if not isinstance(identity, str) or not NAME.fullmatch(identity) or identity == 'builtin':
            raise ConfigurationError(f'invalid or reserved Git source identity: {identity!r}')
        try:
            return _GitSource.model_validate(dict(recipe) if isinstance(recipe, Mapping) else recipe)
        except ValidationError as error:
            raise ConfigurationError(f'invalid Git source recipe for {identity!r}: {error}') from error

    def _state(self):
        if not self.state_path.exists():
            return {'consumer': str(self.consumer_path), 'scope': self.scope, 'selected': {}}
        try:
            state = json.loads(self.state_path.read_text(encoding='utf-8'))
            if state['consumer'] != str(self.consumer_path) or state['scope'] != self.scope:
                raise ConfigurationError('consumer moved: start fresh local state by removing milkpan-state.json and rerunning init')
            if not isinstance(state['selected'], dict):
                raise ValueError('invalid selection map')
            return state
        except (ValueError, KeyError, TypeError) as error:
            raise ConfigurationError(f'invalid milkpan selection state: {error}') from error

    def _write(self, state):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        ignore = self.state_path.parent / '.gitignore'
        previous = ignore.read_text(encoding='utf-8') if ignore.exists() else ''
        if '/milkpan-state.json' not in previous.splitlines():
            replace_bytes(ignore, (previous.rstrip('\n') + '\n/milkpan-state.json\n/milkpan-state.lock\n').encode())
        replace_bytes(self.state_path, (json.dumps(state, indent=2) + '\n').encode())

    @staticmethod
    def _key(source):
        return hashlib.sha256(json.dumps(source.model_dump(), sort_keys=True).encode()).hexdigest()

    @staticmethod
    def _error(identity, error, *, lookup=False):
        code = getattr(error, 'code', type(error).__name__)
        operational = isinstance(error, MilkpanUnavailable) or code in {'not_found', 'unavailable'}
        cls = MetadataUnavailable if lookup and operational else ConfigurationError
        return cls(f'milkpan source {identity!r}: {code}: {error}')

    def _binding(self, identity, source, record, *, deadline=None):
        if record['recipe'] != source.model_dump():
            raise ConfigurationError(f'milkpan recipe mismatch for {identity!r}')
        client = self._milkpan(deadline=deadline)
        lease = client.lease(record['lease'])
        if lease['version'] != record['commit'] or lease['scope'] != self.scope:
            raise ConfigurationError(f'milkpan selection for {identity!r} does not match its lease')
        root = client.path(record['lease']).resolve(strict=True)
        if not root.is_dir():
            raise ConfigurationError(f'milkpan output for {identity!r} is not a directory')
        return SourceBinding(identity, source.origin, source.reference, record['commit'], record['spec'],
                             record['lease'], root)

    def lookup(self, identity, recipe, *, deadline=None):
        source = self._source(identity, recipe)
        record = self._state()['selected'].get(self._key(source))
        if record is None:
            raise MetadataUnavailable(f'Git source {identity!r} has no selected materialization; run init')
        try:
            return self._binding(identity, source, record, deadline=deadline)
        except (MilkpanError, MilkpanUnavailable, OSError) as error:
            raise self._error(identity, error, lookup=True) from error

    @contextmanager
    def _mutation(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        lock = self.state_path.with_suffix('.lock')
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise ConfigurationError(f'milkpan consumer operation already in progress: {lock}') from error
        try:
            os.write(descriptor, str(os.getpid()).encode())
            yield
        finally:
            os.close(descriptor)
            lock.unlink()

    def _prepare(self, identity, source, *, refresh):
        try:
            with self._mutation():
                return self._prepare_locked(identity, source, refresh=refresh)
        except Exception:
            self.reject()
            raise

    def _prepare_locked(self, identity, source, *, refresh):
        state = self._state()
        key = self._key(source)
        if not refresh and key in state['selected']:
            return self._binding(identity, source, state['selected'][key])
        spec = milkpan_spec(source.origin)
        try:
            client = self._milkpan()
            ensure_consumer_policy(self.home, self.scope)
            with stage(f'Resolving source: {identity}') as task:
                candidate = client.acquire(f'{spec}@{source.reference}', scope=candidate_scope(self.scope))
                if refresh and not candidate['fetched']:
                    candidate = client.reacquire(candidate['lease']['id'])
                commit = candidate['lease']['version']
                task.result('resolved', commit)
            if re.fullmatch(r'[0-9a-fA-F]{40}', source.reference) and commit.lower() != source.reference.lower():
                raise ConfigurationError(f'milkpan did not resolve requested commit for {identity!r}')
            with stage(f'Materializing source: {identity}') as task:
                selected = client.acquire(f'{spec}@{commit}', scope=self.scope)
                task.result('downloaded' if selected['fetched'] else 'reused stored content', commit)
            record = {'recipe': source.model_dump(), 'spec': spec, 'commit': commit,
                      'lease': selected['lease']['id'], 'digest': selected['lease']['digest']}
            self._candidates[key] = record
            with stage(f'Verifying source: {identity}'):
                return self._binding(identity, source, record)
        except (MilkpanError, MilkpanUnavailable, OSError) as error:
            raise self._error(identity, error) from error

    def ensure(self, identity, recipe):
        source = self._source(identity, recipe)
        if self._key(source) in self._state()['selected']:
            with stage(f'Checking retained source: {identity}') as task:
                binding = self.lookup(identity, recipe)
                task.result('reused', 'validated retained selection; no refresh')
                return binding
        with stage(f'Preparing source: {identity} (resolution cached up to 24 hours)'):
            return self._prepare(identity, source, refresh=False)

    def acquire(self, identity, recipe):
        with stage(f'Refreshing source: {identity} (explicit request)'):
            return self._prepare(identity, self._source(identity, recipe), refresh=True)

    def commit(self):
        """Publish validated candidates after the caller's success boundary."""
        if not self._candidates:
            return
        with self._mutation():
            self._commit_locked()

    def commit_new(self):
        """Publish validated candidates that replace no prior selection.

        A first selection has no earlier baseline to protect, so publishing it
        before agent provisioning keeps recovery commands usable when that
        provisioning fails. Replacements remain candidates for commit or reject.
        """
        if not self._candidates:
            return
        with self._mutation():
            selected = self._state()['selected']
            self._commit_locked([key for key in self._candidates if key not in selected])

    def _commit_locked(self, keys=None):
        state = self._state()
        keys = list(self._candidates) if keys is None else keys
        replaced = []
        for key in keys:
            previous = state['selected'].get(key)
            if previous and previous['lease'] != self._candidates[key]['lease']:
                replaced.append(previous['lease'])
            state['selected'][key] = self._candidates.pop(key)
        if keys:
            self._write(state)
        self._release_unreferenced(state, replaced)

    def reject(self):
        """Abandon known candidates; their leases go unless a selection uses them."""
        if not self._candidates:
            return
        leases = [candidate['lease'] for candidate in self._candidates.values()]
        self._candidates.clear()
        try:
            with self._mutation():
                self._release_unreferenced(self._state(), leases)
        except ConfigurationError:
            pass

    def _release_unreferenced(self, state, leases):
        """Release leases no selection references; failures only leave a lease behind."""
        referenced = {record['lease'] for record in state['selected'].values()}
        pending = {candidate['lease'] for candidate in self._candidates.values()}
        if self._client is None:
            return
        for lease in leases:
            if lease in referenced or lease in pending:
                continue
            try:
                self._client.release(lease)
            except (MilkpanError, MilkpanUnavailable):
                pass


def _remaining(deadline: float) -> float:
    import time
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise MetadataUnavailable('source lookup deadline exceeded')
    return remaining


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

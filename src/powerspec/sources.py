"""Consumer-scoped retained Saucepan selections; lookup never mutates the store."""
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
from uuid import NAMESPACE_URL, uuid4, uuid5

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from saucepan_sdk import Client, SaucepanError, TransportError

from .catalog import ConfigurationError, MetadataUnavailable, NAME
from .saucepan_tool import ensure_saucepan_binary, inspect_saucepan_binary, inspection_remaining
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


class SaucepanSources:
    """Publish selected pinned generations in the owning consumer's local state."""

    APP = 'powerspec'

    def __init__(self, client: Client | None = None, *, manage_binary=True,
                 consumer_path: Path | None = None, credential_file: str | None = None):
        self._client = client
        self._manage_binary = manage_binary
        self._executable = None
        self._credential_file = credential_file or os.environ.get('POWERSPEC_SAUCEPAN_CREDENTIAL_FILE')
        self.consumer_path = Path(consumer_path or Path.home() / '.powerspec/config.toml').resolve()
        self.scope = 'consumer-' + hashlib.sha256(os.path.normcase(str(self.consumer_path)).encode()).hexdigest()
        self.state_path = self.consumer_path.parent / 'saucepan-state.json'
        self._candidates = {}

    def for_consumer(self, path):
        if Path(path).resolve() == self.consumer_path:
            return self
        return SaucepanSources(self._client, manage_binary=self._manage_binary,
                               consumer_path=path, credential_file=self._credential_file)

    def _client_or_default(self, *, deadline=None):
        if self._client is None:
            with stage('Preparing Saucepan manager' if self._manage_binary else 'Checking Saucepan manager'):
                self._executable = (ensure_saucepan_binary() if self._manage_binary and deadline is None
                                    else inspect_saucepan_binary(**({} if deadline is None else {'deadline': deadline})))
                self._client = Client(executable=str(self._executable))
        if deadline is not None and self._executable is not None:
            return Client(executable=str(self._executable), timeout=inspection_remaining(deadline))
        if deadline is not None:
            inspection_remaining(deadline)
        return self._client

    @staticmethod
    def _source(identity, recipe):
        if not isinstance(identity, str) or not NAME.fullmatch(identity) or identity == 'builtin':
            raise ConfigurationError(f'invalid or reserved Git source identity: {identity!r}')
        try:
            return _GitSource.model_validate(dict(recipe) if isinstance(recipe, Mapping) else recipe)
        except ValidationError as error:
            raise ConfigurationError(f'invalid Git source recipe for {identity!r}: {error}') from error

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
        if parsed.scheme.lower() == 'https' and parsed.netloc.lower() == 'github.com':
            # Saucepan canonicalizes GitHub owner/repository names at registration.
            path = path.lower()
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

    def _state(self):
        if not self.state_path.exists():
            return {'consumer': str(self.consumer_path), 'scope': self.scope, 'selected': {}, 'pending': {}}
        try:
            state = json.loads(self.state_path.read_text(encoding='utf-8'))
            if state['consumer'] != str(self.consumer_path) or state['scope'] != self.scope:
                raise ConfigurationError('consumer moved: explicitly rebind by retaining the old receipt file and starting fresh local state')
            if not isinstance(state['selected'], dict) or not isinstance(state['pending'], dict):
                raise ValueError('invalid binding maps')
            return state
        except (ValueError, KeyError, TypeError) as error:
            raise ConfigurationError(f'invalid Saucepan binding state: {error}') from error

    def _write(self, state):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        ignore = self.state_path.parent / '.gitignore'
        previous = ignore.read_text(encoding='utf-8') if ignore.exists() else ''
        if '/saucepan-state.json' not in previous.splitlines():
            replace_bytes(ignore, (previous.rstrip('\n') + '\n/saucepan-state.json\n/saucepan-state.lock\n').encode())
        replace_bytes(self.state_path, (json.dumps(state, indent=2) + '\n').encode())

    @staticmethod
    def _key(source):
        return hashlib.sha256(json.dumps(source.model_dump(), sort_keys=True).encode()).hexdigest()

    @staticmethod
    def _selector(source):
        return ({'type': 'commit', 'commit': source.reference} if re.fullmatch(r'[0-9a-fA-F]{40}', source.reference)
                else {'type': 'ref', 'reference': source.reference})

    def _bound(self, state, *, deadline=None):
        if not state.get('app'):
            raise MetadataUnavailable('Powerspec Saucepan application is unavailable; run init')
        return self._client_or_default(deadline=deadline).for_app(state['app'], credential_file=self._credential_file)

    @staticmethod
    def _error(identity, error, *, lookup=False):
        kind = getattr(error, 'code', getattr(error, 'kind', type(error).__name__))
        uncertain = ' (mutation may have committed; original receipt retained)' if getattr(error, 'indeterminate', False) else ''
        cls = MetadataUnavailable if lookup else ConfigurationError
        return cls(f'Saucepan source {identity!r}: {kind}{uncertain}')

    def _read(self, state, method, *args, deadline=None, **kwargs):
        return getattr(self._bound(state, deadline=deadline), method)(*args, **kwargs)

    def _binding(self, identity, source, state, record, *, deadline=None):
        if record['recipe'] != source.model_dump():
            raise ConfigurationError(f'Saucepan recipe mismatch for {identity!r}')
        pin = self._read(state, 'pin', record['pin'], deadline=deadline)
        output = record['output']
        if pin['owner'] != state['app'] or pin['state'] != 'active' or not pin['outputs'].get(output, {}).get('available'):
            raise MetadataUnavailable(f'Saucepan retained output for {identity!r} is unavailable')
        receipt = pin.get('group')
        if not receipt or receipt['group']['uuid'] != record['group']:
            raise ConfigurationError('Saucepan pin receipt does not match selected group')
        selected = receipt['group']['selected']['members']['repository']
        if selected['scope'] != self.scope or selected['output_uuid'] != output or selected.get('claim_uuid') != record.get('claim'):
            raise ConfigurationError('Saucepan selected output scope or identity mismatch')
        target = receipt['group']['definition']['members'][0]['target']
        if (target['type'] != 'acquire' or target['source_uuid'] != record['source']
            or target['selector'] != self._selector(source) or target.get('selection', {}).get('folder')):
            raise ConfigurationError('Saucepan output provenance mismatch')
        resolved = selected['selected_source']
        if resolved['type'] != 'git' or resolved['commit'] != record['commit'] or not re.fullmatch(r'[0-9a-fA-F]{40}', resolved['commit']):
            raise ConfigurationError('Saucepan resolved revision mismatch')
        if self._selector(source)['type'] == 'commit' and resolved['commit'].lower() != source.reference.lower():
            raise ConfigurationError('Saucepan did not resolve requested commit')
        # Pin inspection returns the immutable retained output's path. Never
        # resolve a moving claim or reconstruct Saucepan's storage layout here.
        root = Path(pin['outputs'][output]['path']).resolve(strict=True)
        relative = selected.get('relative')
        if relative:
            candidate = (root / relative).resolve(strict=True)
            if not candidate.is_relative_to(root):
                raise ConfigurationError('Saucepan returned an escaping relative view')
            root = candidate
        if not root.is_dir():
            raise ConfigurationError('Saucepan output is not a directory')
        return SourceBinding(identity, source.origin, source.reference, resolved['commit'], record['source'], output, root)

    def lookup(self, identity, recipe, *, deadline=None):
        source = self._source(identity, recipe)
        state = self._state()
        record = state['selected'].get(self._key(source))
        if record is None:
            raise MetadataUnavailable(f'Git source {identity!r} has no selected materialization; run init')
        try:
            return self._binding(identity, source, state, record, deadline=deadline)
        except (SaucepanError, TransportError, OSError, KeyError, TypeError, ValueError) as error:
            if isinstance(error, ConfigurationError):
                raise
            raise self._error(identity, error, lookup=True) from error

    def _application(self, state):
        client = self._client_or_default()
        if not state.get('app'):
            request = {'registration_key': self.APP, 'name': self.APP, 'credentials_required': False}
            try:
                registered = client.register_application(request)
            except SaucepanError as error:
                if error.code != 'unsupported_store':
                    raise
                # Rust refuses initialization over incompatible/nonempty stores.
                client.init()
                registered = client.register_application(request)
            state['app'] = registered['uuid']
            self._write(state)
        return self._bound(state)

    def _policies(self, refresh):
        """Expand manager defaults while keeping app-owned choices explicit."""
        def policy(definition):
            identity = str(uuid5(NAMESPACE_URL, 'powerspec:' + json.dumps(definition, sort_keys=True)))
            return dict(uuid=identity, **definition)

        options = {}
        if refresh:
            update = policy({'type': 'update_policy', 'mode': 'always'})
            options = {'catalog': [update], 'acquisition_policy_refs': [update['uuid']]}
        expansion = self._client_or_default().profile('explicit-update', **options)
        pin = policy({'type': 'pin_policy', 'retention': 'until_released'})
        return {'catalog': [*expansion['catalog'], pin],
                'policy_refs': expansion['combined_policy_refs'], 'pin_refs': [pin['uuid']]}

    @contextmanager
    def _mutation(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        lock = self.state_path.with_suffix('.lock')
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise ConfigurationError(f'Saucepan consumer operation already in progress: {lock}') from error
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
            return self._binding(identity, source, state, state['selected'][key])
        try:
            app = self._application(state)
            pending = state['pending'].get(key)
            if pending is None:
                policies = self._policies(refresh)
                registered = self._client_or_default().register_source({'type': 'git', 'origin': source.origin})
                if registered['source'].get('type') != 'git' or not self._same_source(source, _GitSource(provider='git', origin=registered['source'].get('origin'), reference=source.reference)):
                    raise ConfigurationError('Saucepan registered a mismatched source')
                operation = str(uuid4())
                pending = {'recipe': source.model_dump(), 'source': registered['uuid'],
                           'key': f'{self.scope}:{operation}', 'refresh': refresh, 'policies': policies}
                state['pending'][key] = pending
                self._write(state)
            elif pending['recipe'] != source.model_dump() or pending['refresh'] != refresh:
                raise ConfigurationError('pending source operation requires reconciliation before another intent')
            # A recipe can evolve between invocations. Retry the saved expanded
            # definitions and references, never a fresh recipe with the old key.
            policies = pending['policies']
            self._client_or_default().register_policies(policies['catalog'])
            if refresh:
                matches = app.query_claims({'app': state['app'], 'scope': self.scope, 'where': []})
                wanted = policies['policy_refs']
                claims = [item['claim'] for item in matches['claims']
                          if item['claim']['request']['source_uuid'] == pending['source']
                          and item['claim']['request']['selector'] == self._selector(source)]
                if len(claims) > 1:
                    raise ConfigurationError('ambiguous matching scoped claims')
                if claims and claims[0]['policy_refs'] != wanted:
                    app.adopt_claim_policies(state['app'], claims[0]['uuid'], matches['revision'], wanted)
            definition = {'registration_key': pending['key'], 'members': [{'name': 'repository', 'target': {
                'type': 'acquire', 'source_uuid': pending['source'], 'selector': self._selector(source),
                'policy_refs': policies['policy_refs'], 'claim': {'scope': self.scope}}}]}
            if 'group' not in pending:
                groups = app.list_groups(key=pending['key'])
                if len(groups) > 1:
                    raise ConfigurationError('ambiguous Saucepan group registration')
                group = groups[0] if groups else app.register_group(definition)
                target = group['definition']['members'][0]['target']
                intended = definition['members'][0]['target']
                if (len(group['definition']['members']) != 1 or target['source_uuid'] != intended['source_uuid']
                    or target['selector'] != intended['selector'] or target['claim']['scope'] != self.scope
                    or target['policy_refs'] != intended['policy_refs']):
                    raise ConfigurationError('Saucepan group intent mismatch')
                pending.update(group=group['uuid'], expected_revision=group['revision'])
                self._write(state)
            # Same receipt key and original revision make retry reconciliation
            # idempotent even after a committed result was lost.
            with stage(f'Materializing source: {identity}'):
                prepared = app.prepare_group(pending['group'], expected_revision=pending['expected_revision'],
                    pin={'registration_key': pending['key'], 'policy_refs': policies['pin_refs']})
            member = prepared['resources']['members']['repository']
            resolved = prepared['group']['selected']['members']['repository']['selected_source']
            record = {**pending, 'pin': prepared['pin']['uuid'], 'output': member['output_uuid'],
                      'commit': resolved['commit'], 'claim': member.get('claim_uuid')}
            self._candidates[key] = record
            with stage(f'Verifying source: {identity}'):
                binding = self._binding(identity, source, state, record)
            return binding
        except (SaucepanError, TransportError, OSError, KeyError, TypeError, ValueError) as error:
            if isinstance(error, ConfigurationError):
                raise
            raise self._error(identity, error) from error

    def ensure(self, identity, recipe):
        source = self._source(identity, recipe)
        if self._key(source) in self._state()['selected']:
            return self.lookup(identity, recipe)
        return self._prepare(identity, source, refresh=False)

    def acquire(self, identity, recipe):
        return self._prepare(identity, self._source(identity, recipe), refresh=True)

    def commit(self):
        """Publish validated candidates after the caller's success boundary."""
        if not self._candidates:
            return
        with self._mutation():
            self._commit_locked()

    def _commit_locked(self):
        state = self._state()
        for key, candidate in self._candidates.items():
            if state['pending'].get(key, {}).get('key') != candidate['key']:
                raise ConfigurationError('source preparation changed before publication')
            state['selected'][key] = candidate
            del state['pending'][key]
        self._write(state)
        self._candidates.clear()

    def reject(self):
        """Abandon known candidates, retaining their pins; uncertain work stays."""
        if not self._candidates:
            return
        with self._mutation():
            state = self._state()
            for key, candidate in self._candidates.items():
                if state['pending'].get(key, {}).get('key') == candidate['key']:
                    del state['pending'][key]
            self._write(state)
            self._candidates.clear()


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

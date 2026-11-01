"""An in-memory milkpan for source-store tests."""
from pathlib import Path
import uuid

from powerspec.milkpan_client import MilkpanError


class FakeMilkpan:
    """Leases keyed by (spec, scope); `refs` maps `<spec>@<ref>` to a commit."""

    def __init__(self, home: Path):
        self.home, self.timeout, self.env = str(home), None, {}
        self.refs, self.leases_by_id, self.stored, self.calls = {}, {}, set(), []

    def with_timeout(self, timeout):
        return self

    def _resolve(self, spec):
        source, _, selector = spec.rpartition('@')
        commit = selector if len(selector) == 40 else self.refs[f'{source}@{selector}']
        return source, commit

    def acquire(self, spec, *, scope):
        self.calls.append(('acquire', spec, scope))
        source, commit = self._resolve(spec)
        existing = next((l for l in self.leases_by_id.values() if l['spec'] == spec and l['scope'] == scope), None)
        fetched = (source, commit) not in self.stored
        self.stored.add((source, commit))
        lease = existing or {'id': str(uuid.uuid4()), 'spec': spec, 'scope': scope}
        lease.update(version=commit, digest=f'{commit:0<64}'[:64])
        self.leases_by_id[lease['id']] = lease
        return {'lease': dict(lease), 'path': str(self._dir(source, commit)), 'fetched': fetched}

    def reacquire(self, lease):
        self.calls.append(('reacquire', lease))
        current = self.leases_by_id[lease]
        result = self.acquire(current['spec'], scope=current['scope'])
        return {**result, 'fetched': True}

    def release(self, lease):
        self.calls.append(('release', lease))
        if lease not in self.leases_by_id:
            raise MilkpanError('not_found', 'no live lease', {'lease': lease})
        return {'released': self.leases_by_id.pop(lease)}

    def lease(self, lease):
        if lease not in self.leases_by_id:
            raise MilkpanError('not_found', 'no live lease', {'lease': lease})
        return dict(self.leases_by_id[lease])

    def path(self, lease):
        current = self.lease(lease)
        return self._dir(*self._resolve(current['spec']))

    def _dir(self, source, commit):
        path = Path(self.home) / 'trees' / commit
        path.mkdir(parents=True, exist_ok=True)
        return path

"""Powerspec's managed milkpan: a pinned, verified release that manages itself.

The first preparation downloads the pinned release asset, verifies its SHA-256
and uses it once to acquire milkpan's own release in scope `powerspec-manager`
and link it as `milkpan`. Later runs use the link. When Powerspec pins a newer
release, the next preparation repoints the link, effective on the next run.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import tarfile
import tempfile
import urllib.request
import zipfile

from .catalog import ConfigurationError, MetadataUnavailable
from .milkpan_client import Milkpan, MilkpanError, MilkpanUnavailable

MANAGER_SCOPE = 'powerspec-manager'
SUPPORTED_LINES = {(0, 2)}
DOWNLOAD_LIMIT = 64 * 1024 * 1024
LEASE_ACTIONS = ['acquire', 'reacquire', 'read', 'release']

TARGETS = {
    ('Windows', 'x86_64'): 'x86_64-pc-windows-msvc',
    ('Darwin', 'arm64'): 'aarch64-apple-darwin',
    ('Darwin', 'x86_64'): 'x86_64-apple-darwin',
    ('Linux', 'x86_64'): 'x86_64-unknown-linux-gnu',
}
MACHINES = {'amd64': 'x86_64', 'x64': 'x86_64', 'aarch64': 'arm64'}


@dataclass(frozen=True)
class Release:
    """A pinned milkpan release: per-target asset digests from its SHA256SUMS."""
    tag: str
    digests: dict[str, str]
    download_base: str = 'https://github.com/ZackaryW/milkpan/releases/download'
    github_api: str | None = None
    env: dict[str, str] = field(default_factory=dict)

    def target(self, system: str | None = None, machine: str | None = None) -> str:
        system = system or platform.system()
        machine = (machine or platform.machine()).lower()
        target = TARGETS.get((system, MACHINES.get(machine, machine)))
        if target is None:
            supported = ', '.join(f'{s}/{m}' for s, m in TARGETS)
            raise ConfigurationError(f'unsupported milkpan platform {system}/{machine}; supported: {supported}')
        return target

    def asset(self, target: str) -> tuple[str, str]:
        extension = 'zip' if 'windows' in target else 'tar.gz'
        name = f'milkpan-{self.tag}-{target}.{extension}'
        digest = self.digests.get(name)
        if digest is None:
            raise ConfigurationError(f'no pinned digest for {name}')
        return name, digest

    def spec(self, target: str) -> str:
        return f'github-release:zackaryw/milkpan@{self.tag}#{self.asset(target)[0]}'

    def client_env(self) -> dict[str, str]:
        return {**self.env, **({'MILKPAN_GITHUB_API': self.github_api} if self.github_api else {})}


MILKPAN = Release(tag='v0.2.0', digests={
    'milkpan-v0.2.0-aarch64-apple-darwin.tar.gz': 'c4f20bf9f0425e2852abb4effbca23ba26570ad6572303a26db22a3c9fdaba6c',
    'milkpan-v0.2.0-x86_64-apple-darwin.tar.gz': '0f0d1a925b112d3afabc32a42a1c6818a3151248228f80be6b059f2427c025f7',
    'milkpan-v0.2.0-x86_64-pc-windows-msvc.zip': 'b6f10ea5a77ab50b181606876e1a188ac47113383cafc3708b190c09066c6fdc',
    'milkpan-v0.2.0-x86_64-unknown-linux-gnu.tar.gz': '039ad9b610c4eec50aa0694db37659db12d4e1196434b776de3e33a6aee9bc4f',
})


def executable_name() -> str:
    return 'milkpan.exe' if os.name == 'nt' else 'milkpan'


def default_home() -> Path:
    override = os.environ.get('POWERSPEC_MILKPAN_HOME')
    return Path(override) if override else Path.home() / '.powerspec' / 'milkpan'


def link_executable(home: Path) -> Path:
    return home / 'links' / 'milkpan' / executable_name()


def standalone() -> Path | None:
    override = os.environ.get('POWERSPEC_MILKPAN')
    return Path(override) if override else None


def _version_line(text: str):
    try:
        major, minor, *_ = text.split('.')
        return int(major), int(minor)
    except ValueError:
        return None


def check_compatible(client: Milkpan) -> None:
    """Protocol 1 and a supported release line, or a configuration error."""
    try:
        supported = client.protocol().get('supported', [])
        version = client.version()
    except (MilkpanError, MilkpanUnavailable) as error:
        raise ConfigurationError(f'milkpan at {client.executable} is not usable: {error}') from error
    if 1 not in supported or _version_line(version) not in SUPPORTED_LINES:
        lines = ', '.join(f'{a}.{b}' for a, b in sorted(SUPPORTED_LINES))
        raise ConfigurationError(f'milkpan {version} at {client.executable} is incompatible: Powerspec needs '
                                 f'protocol 1 and release line {lines}; update milkpan or unset POWERSPEC_MILKPAN')


# ---- download, verification and extraction ---------------------------------------------------

def download(url: str, destination: Path, expected: str) -> None:
    """Stream `url` to `destination`, rejecting it unless its SHA-256 matches."""
    digest, size = hashlib.sha256(), 0
    with urllib.request.urlopen(url, timeout=60) as response, destination.open('wb') as out:
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > DOWNLOAD_LIMIT:
                raise ConfigurationError(f'milkpan download exceeds {DOWNLOAD_LIMIT} bytes: {url}')
            digest.update(chunk)
            out.write(chunk)
    if digest.hexdigest() != expected:
        destination.unlink(missing_ok=True)
        raise ConfigurationError(f'milkpan download checksum mismatch for {url}')


def _safe(name: str) -> PurePosixPath:
    path = PurePosixPath(name.replace('\\', '/'))
    if path.is_absolute() or '..' in path.parts or (path.parts and ':' in path.parts[0]):
        raise ConfigurationError(f'unsafe member in milkpan archive: {name}')
    return path


def extract(archive: Path, directory: Path) -> Path:
    """Extract a release archive and return the milkpan executable inside it."""
    if archive.name.endswith('.zip'):
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.namelist():
                _safe(member)
            bundle.extractall(directory)
    else:
        with tarfile.open(archive, 'r:gz') as bundle:
            for member in bundle.getmembers():
                _safe(member.name)
                if not (member.isfile() or member.isdir()):
                    raise ConfigurationError(f'unsupported member in milkpan archive: {member.name}')
            bundle.extractall(directory, filter='data')
    found = [path for path in directory.rglob(executable_name()) if path.is_file()]
    if len(found) != 1:
        raise ConfigurationError('milkpan archive does not contain exactly one executable')
    if os.name != 'nt':
        found[0].chmod(0o755)
    return found[0]


# ---- policy owned by Powerspec ---------------------------------------------------------------

@contextmanager
def _locked(home: Path):
    home.mkdir(parents=True, exist_ok=True)
    lock = home / 'powerspec.lock'
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ConfigurationError(f'another Powerspec process is changing {home}: {lock}') from error
    try:
        yield
    finally:
        os.close(descriptor)
        lock.unlink()


def _rule(scope, actions, resources, lease=None):
    lines = ['[[rule]]', f'scope = {json.dumps(scope)}', 'effect = "allow"',
             f'actions = {json.dumps(actions)}', f'resources = {json.dumps(resources)}']
    if lease:
        params = ', '.join(f'{key} = {json.dumps(value)}' for key, value in lease.items())
        lines.append(f'obligations = [{{ name = "lease", params = {{ {params} }} }}]')
    return '\n'.join(lines)


def candidate_scope(scope: str) -> str:
    return f'{scope}-candidates'


def write_policy(home: Path, consumer_scopes: set[str]) -> None:
    rules = [_rule(MANAGER_SCOPE, [*LEASE_ACTIONS, 'link'], ['github-release:zackaryw/milkpan@*'])]
    for scope in sorted(consumer_scopes):
        rules.append(_rule(scope, LEASE_ACTIONS, ['github:*', 'local:*'], {'ttl': '36500d'}))
        rules.append(_rule(candidate_scope(scope), LEASE_ACTIONS, ['github:*', 'local:*'],
                           {'refresh': '1d', 'ttl': '7d'}))
    header = '# Generated by Powerspec; edits are overwritten.\n\n'
    temporary = home / 'milkpan.toml.tmp'
    temporary.write_text(header + '\n\n'.join(rules) + '\n', encoding='utf-8')
    os.replace(temporary, home / 'milkpan.toml')


def ensure_consumer_policy(home: Path, scope: str) -> None:
    """Allow `scope` (and its candidate scope) before its first acquisition."""
    with _locked(home):
        registry = home / 'powerspec-scopes.json'
        scopes = set(json.loads(registry.read_text(encoding='utf-8'))) if registry.exists() else set()
        if scope in scopes and (home / 'milkpan.toml').exists():
            return
        scopes.add(scope)
        write_policy(home, scopes)
        registry.write_text(json.dumps(sorted(scopes)), encoding='utf-8')


def _known_scopes(home: Path) -> set[str]:
    registry = home / 'powerspec-scopes.json'
    return set(json.loads(registry.read_text(encoding='utf-8'))) if registry.exists() else set()


# ---- ensure / inspect ------------------------------------------------------------------------

def _client(executable: Path, home: Path, release: Release) -> Milkpan:
    return Milkpan(executable, home, env=release.client_env())


def manager_state(client: Milkpan, release: Release, target: str) -> str:
    """`current`, `behind` (another release is linked) or `absent`."""
    try:
        leases = client.leases(scope=MANAGER_SCOPE)
    except (MilkpanError, MilkpanUnavailable):
        return 'absent'
    _, digest = release.asset(target)
    if any(lease['digest'] == digest for lease in leases):
        return 'current'
    return 'behind' if leases else 'absent'


def inspect_milkpan(home: Path | None = None, *, release: Release = MILKPAN, timeout: float | None = None) -> Milkpan:
    """A usable client without provisioning anything; MetadataUnavailable otherwise."""
    home = home or default_home()
    executable = standalone() or link_executable(home)
    if not executable.is_file():
        raise MetadataUnavailable('Powerspec milkpan is not prepared; run init')
    client = _client(executable, home, release).with_timeout(timeout)
    try:
        check_compatible(client)
    except ConfigurationError as error:
        raise MetadataUnavailable(str(error)) from error
    return client


def ensure_milkpan(home: Path | None = None, *, release: Release = MILKPAN) -> Milkpan:
    """A usable client, bootstrapping or repointing the managed milkpan as needed."""
    home = home or default_home()
    override = standalone()
    if override is not None:
        client = _client(override, home, release)
        check_compatible(client)
        return client
    target = release.target()
    linked = link_executable(home)
    current = None
    if linked.is_file():
        candidate = _client(linked, home, release)
        try:
            check_compatible(candidate)
            current = candidate
        except ConfigurationError:
            current = None
        if current is not None and manager_state(current, release, target) == 'current':
            return current
    with _locked(home):
        write_policy(home, _known_scopes(home))
    if current is not None:
        _self_link(current, release, target)
        return current
    name, digest = release.asset(target)
    with tempfile.TemporaryDirectory(prefix='powerspec-milkpan-') as directory:
        staging = Path(directory).resolve()
        if staging.is_relative_to(home.resolve()):
            raise ConfigurationError('milkpan bootstrap staging must be outside the milkpan home')
        archive = staging / name
        download(f'{release.download_base}/{release.tag}/{name}', archive, digest)
        bootstrap = _client(extract(archive, staging / 'extracted'), home, release)
        check_compatible(bootstrap)
        _self_link(bootstrap, release, target)
    client = _client(linked, home, release)
    check_compatible(client)
    return client


def _self_link(client: Milkpan, release: Release, target: str) -> None:
    _, digest = release.asset(target)
    try:
        acquired = client.acquire(release.spec(target), scope=MANAGER_SCOPE)
        lease = acquired['lease']['id']
        if acquired['lease']['digest'] != digest:
            client.release(lease)
            raise ConfigurationError('managed milkpan release digest does not match the pin')
        try:
            client.link(lease, name='milkpan', file=executable_name())
        except MilkpanError as error:
            if error.code != 'conflict':
                raise
            # The link follows the previous release's lease: move it to the new
            # lease, then let the old release go. Running processes keep it;
            # an interruption here only means the next run bootstraps again.
            previous = error.details.get('lease')
            # Run from the resolved file: the link path disappears while unlinking.
            stable = Milkpan(Path(client.executable).resolve(), client.home, timeout=client.timeout, env=client.env)
            stable.result('unlink', 'milkpan')
            stable.link(lease, name='milkpan', file=executable_name())
            if previous:
                stable.release(previous)
    except (MilkpanError, MilkpanUnavailable) as error:
        raise ConfigurationError(f'cannot prepare managed milkpan: {error}') from error

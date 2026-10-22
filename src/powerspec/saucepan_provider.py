"""Pinned provider identity and the managed-setup wire boundary."""
from dataclasses import dataclass
import os
from pathlib import Path
import platform
import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


@dataclass(frozen=True)
class Provider:
    tag: str
    sdk_revision: str
    windows_sha256: str
    unix_sha256: str
    release_base: str = 'https://github.com/ZackaryW/saucepan/releases/download'
    fixture_api: str | None = None

    def __post_init__(self):
        if not re.fullmatch(r'v\d+\.\d+\.\d+', self.tag):
            raise ValueError('provider requires an exact release tag')
        for value, length in ((self.sdk_revision, 40), (self.windows_sha256, 64), (self.unix_sha256, 64)):
            if not re.fullmatch(r'[0-9a-f]{' + str(length) + '}', value) or len(set(value)) == 1:
                raise ValueError('provider requires immutable non-placeholder identities')
        if self.fixture_api is None:
            if self.release_base != 'https://github.com/ZackaryW/saucepan/releases/download':
                raise ValueError('production provider endpoint is fixed')
        elif not (re.fullmatch(r'http://(?:127\.0\.0\.1|localhost):\d+', self.fixture_api)
                  and re.fullmatch(r'http://(?:127\.0\.0\.1|localhost):\d+(?:/[^?#]*)?', self.release_base)):
            raise ValueError('explicit fixture endpoints must be loopback HTTP')

    def installer(self, system=None, machine=None):
        system, machine = system or platform.system(), (machine or platform.machine()).lower()
        supported = {'Windows': {'amd64', 'x86_64', 'arm64', 'aarch64', 'x86', 'i686'},
                     'Darwin': {'arm64', 'aarch64', 'x86_64'}, 'Linux': {'x86_64', 'amd64'}}
        if machine not in supported.get(system, set()):
            raise ValueError(f'unsupported Saucepan installer platform: {system}/{machine}')
        name, digest = ('install.ps1', self.windows_sha256) if system == 'Windows' else ('install.sh', self.unix_sha256)
        return name, f'{self.release_base}/{self.tag}/{name}', digest


PROVIDER = Provider(
    tag='v0.11.0', sdk_revision='324282bac14fd0e0032a07e0fbed85ee95447dbb',
    windows_sha256='40bfe6d67766b1f0f31cd87847ed982dcf910b789dcb930cd66b119047f3e471',
    unix_sha256='2930797ce66a7b43f5670643451a461d711dd2effa1db389a39fc8178aacc696',
)


def same_path(left, right):
    def canonical(value):
        path = str(Path(value).resolve())
        if os.name == 'nt':
            if path.startswith('\\\\?\\UNC\\'):
                path = '\\\\' + path[8:]
            elif path.startswith('\\\\?\\'):
                path = path[4:]
        return os.path.normcase(path)
    return canonical(left) == canonical(right)


class SetupIdentity(BaseModel):
    model_config = ConfigDict(strict=True, extra='ignore')
    schema_version: int
    root: str
    launcher_path: str | None
    app: str | None
    claim: str | None
    output: str | None
    installed_version: str | None
    operation: str | None
    diagnostics: list[str]

    @model_validator(mode='after')
    def identity(self):
        if self.schema_version != 1 or not self.root or not Path(self.root).is_absolute():
            raise ValueError('unsupported setup schema or root')
        for field in ('app', 'claim', 'output', 'operation'):
            value = getattr(self, field)
            if value is not None and str(UUID(value)) != value.lower():
                raise ValueError(f'invalid {field} UUID')
        for field in ('launcher_path', 'installed_version'):
            if getattr(self, field) == '':
                raise ValueError(f'empty {field}')
        if self.launcher_path is not None and not Path(self.launcher_path).is_absolute():
            raise ValueError('setup launcher must be absolute')
        return self

    def check_target(self, target):
        if not same_path(self.root, target.parent.parent):
            raise ValueError('setup root mismatch')
        if self.launcher_path is not None and not same_path(self.launcher_path, target):
            raise ValueError('setup launcher mismatch')

    def require_binding(self):
        if any(getattr(self, key) is None for key in ('app', 'claim', 'output', 'launcher_path', 'installed_version')):
            raise ValueError('ready setup requires complete binding identities')


class SetupStatus(SetupIdentity):
    state: Literal['absent', 'unmanaged', 'ready', 'pending', 'conflict']

    @model_validator(mode='after')
    def readiness(self):
        if self.state == 'ready':
            self.require_binding()
        return self


class SetupOutcome(SetupIdentity):
    status: Literal['preparing', 'commit_intent', 'cleanup_pending', 'complete', 'failed', 'conflict']
    changed: bool
    operation: str
    lifecycle_operation: str | None
    backup_paths: list[str]
    retry_shim: str | None

    @model_validator(mode='after')
    def completion(self):
        if self.lifecycle_operation is not None and str(UUID(self.lifecycle_operation)) != self.lifecycle_operation.lower():
            raise ValueError('invalid lifecycle operation UUID')
        if self.status == 'complete':
            self.require_binding()
        return self

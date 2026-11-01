"""A thin client for milkpan's command-line protocol (panned's shared envelope)."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any

PROTOCOL = 1


class MilkpanUnavailable(Exception):
    """The executable could not be run or answered outside the protocol."""


@dataclass
class MilkpanError(Exception):
    """An `ok: false` envelope: a stable code, a message and structured details."""
    code: str
    message: str
    details: dict[str, Any]

    def __str__(self):
        return f'{self.code}: {self.message}'


class Milkpan:
    """One subprocess per call: `<exe> --home <home> --format json --protocol 1 ...`."""

    def __init__(self, executable: Path | str, home: Path | str, *, timeout: float | None = 600):
        self.executable, self.home, self.timeout = str(executable), str(home), timeout

    def with_timeout(self, timeout: float | None) -> Milkpan:
        return Milkpan(self.executable, self.home, timeout=timeout)

    def _run(self, *arguments: str) -> tuple[int, Any]:
        argv = [self.executable, '--home', self.home, '--format', 'json', '--protocol', str(PROTOCOL), *arguments]
        try:
            process = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8', errors='replace',
                                     timeout=self.timeout, shell=False,
                                     creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except subprocess.TimeoutExpired as error:
            raise MilkpanUnavailable(f'milkpan timed out after {self.timeout}s: {" ".join(arguments)}') from error
        except OSError as error:
            raise MilkpanUnavailable(f'cannot run milkpan {self.executable}: {error}') from error
        text = process.stdout if process.stdout.strip() else process.stderr
        try:
            envelope = json.loads(text)
            ok = envelope['ok']
        except (ValueError, KeyError, TypeError) as error:
            raise MilkpanUnavailable(f'milkpan answered outside the protocol (exit {process.returncode})') from error
        if not ok:
            failure = envelope.get('error') or {}
            raise MilkpanError(str(failure.get('code', 'internal')), str(failure.get('message', '')),
                               dict(failure.get('details') or {}))
        return process.returncode, envelope.get('result')

    def result(self, *arguments: str) -> Any:
        return self._run(*arguments)[1]

    def protocol(self) -> dict:
        return self.result('protocol')

    def version(self) -> str:
        """The `--version` line's version, outside the envelope."""
        try:
            process = subprocess.run([self.executable, '--version'], capture_output=True, text=True,
                                     encoding='utf-8', errors='replace', timeout=self.timeout, shell=False,
                                     creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except (OSError, subprocess.TimeoutExpired) as error:
            raise MilkpanUnavailable(f'cannot run milkpan {self.executable}: {error}') from error
        parts = process.stdout.split()
        if process.returncode != 0 or len(parts) < 2:
            raise MilkpanUnavailable(f'milkpan --version answered unexpectedly (exit {process.returncode})')
        return parts[1]

    def acquire(self, spec: str, *, scope: str) -> dict:
        return self.result('acquire', spec, '--scope', scope)

    def reacquire(self, lease: str) -> dict:
        return self.result('reacquire', lease)

    def release(self, lease: str) -> dict:
        return self.result('release', lease)

    def lease(self, lease: str) -> dict:
        return self.result('lease', 'show', lease)

    def leases(self, *, scope: str | None = None) -> list[dict]:
        arguments = ['lease', 'list'] + (['--scope', scope] if scope else [])
        return self.result(*arguments)['leases']

    def path(self, lease: str) -> Path:
        return Path(self.result('path', lease)['path'])

    def link(self, lease: str, *, name: str, file: str | None = None) -> dict:
        return self.result('link', lease, '--name', name, *(['--file', file] if file else []))

"""Observe guidance stages without changing host trust or claiming receipt."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tomllib
from ruamel.yaml.error import YAMLError

from .catalog import ConfigurationError, SAFE_YAML
from .doctoring import DoctorCheck
from .hooks import callback_for, native_document
from .workspace import open_workspace


EVENTS = ('sessionStart', 'afterCompaction')
ZMEM = '@builtin/zmem-lifecycle'


def _plain(body: str) -> str:
    return re.sub(r'<skill:([^>]+)>', r'\1', body).strip()


def _contains(text: str, body: str) -> bool:
    return ' '.join(body.split()) in ' '.join(text.split())


def _persistent_check(consumer, body):
    path = consumer.config_path.parent.parent / 'config.yaml'
    try:
        document = SAFE_YAML.load(path.read_text(encoding='utf-8-sig'))
        context = document.get('context') if isinstance(document, dict) else None
        if not isinstance(context, str) or not _contains(context, body):
            raise ValueError('current standing memory rule is missing or stale; run pspec sync')
    except (OSError, ValueError, YAMLError) as error:
        # YAML parser diagnostics, I/O and invalid shapes are observations.
        return DoctorCheck('guidance-context', 'failed', f'{path}: {error}')
    return DoctorCheck('guidance-context', 'ok', f'current standing rule published in {path}')


def _native_checks(agent: str):
    directory = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex') if agent == 'codex' else (
        Path(os.environ.get('CLAUDE_CONFIG_DIR') or Path.home() / '.claude'))
    path = directory / ('hooks.json' if agent == 'codex' else 'settings.json')
    try:
        document = json.loads(path.read_text(encoding='utf-8-sig'))
        entries = document.get('hooks', {}).get('SessionStart', [])
        if not isinstance(entries, list):
            raise ValueError('hooks.SessionStart must be a list')
    except (OSError, ValueError, AttributeError) as error:
        return [DoctorCheck(f'hooks-{event}', 'failed', f'{path}: {error}') for event in EVENTS]

    checks, matching = [], []
    for event, expected in zip(EVENTS, native_document(agent)['hooks']['SessionStart']):
        command = expected['hooks'][0]['command']
        found = []
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict) or entry.get('matcher') != expected['matcher']:
                continue
            handlers = entry.get('hooks', [])
            if not isinstance(handlers, list):
                continue
            for j, handler in enumerate(handlers):
                if isinstance(handler, dict) and handler.get('type') == 'command' and handler.get('command') == command:
                    found.append((i, j))
        matching.extend(found)
        checks.append(DoctorCheck(f'hooks-{event}', 'ok' if found else 'failed',
                                  f'{path}: expected registration ' + ('present' if found else 'missing; run pspec init --agent ' + agent)))

    settings_path = directory / ('config.toml' if agent == 'codex' else 'settings.json')
    try:
        if agent == 'codex':
            settings = tomllib.loads(settings_path.read_text(encoding='utf-8-sig')) if settings_path.exists() else {}
            states = settings.get('hooks', {}).get('state', {})
            if not isinstance(states, dict):
                raise ValueError('hooks.state must be a table')
            keys = {os.path.normcase(f'{path}:session_start:{i}:{j}') for i, j in matching}
            disabled = settings.get('features', {}).get('codex_hooks') is False or any(
                os.path.normcase(key) in keys and isinstance(value, dict) and value.get('enabled') is False
                for key, value in states.items())
        else:
            disabled = document.get('disableAllHooks') is True
        checks.append(DoctorCheck('hooks-settings', 'failed' if disabled else 'warning',
            f'{settings_path}: explicit disabled setting observed' if disabled else
            'no disabling user setting observed; effective host enablement and trust remain unverified'))
    except (OSError, ValueError, AttributeError) as error:
        checks.append(DoctorCheck('hooks-settings', 'failed', f'{settings_path}: {error}'))
    return checks


def _generation_check(cwd, agent, event, body, inspect):
    result = inspect(['pspec', 'resolve', 'hook', event, '--agent', agent], cwd=cwd, timeout=5)
    name = f'guidance-{event}'
    if not result.ok:
        return DoctorCheck(name, 'failed', f'resolver {result.kind}: {result.stderr.strip()}')
    try:
        if not result.stdout.strip() and body is None:
            return DoctorCheck(name, 'ok', 'resolver produced no guidance; no standing memory trait selected')
        output = json.loads(result.stdout)['hookSpecificOutput']
        if output['hookEventName'] != 'SessionStart' or not isinstance(output['additionalContext'], str):
            raise ValueError('invalid SessionStart context envelope')
        if body is not None and not _contains(output['additionalContext'], body):
            raise ValueError('resolver omitted or changed the selected standing memory rule')
    except (ValueError, KeyError, TypeError) as error:
        return DoctorCheck(name, 'failed', f'invalid resolver output: {error}')
    detail = 'resolver generated context; host receipt not established'
    if result.stderr.strip():
        detail += '; ' + result.stderr.strip()
    return DoctorCheck(name, 'ok', detail)


def inspect_guidance(cwd: Path, agent: str, *, inspect) -> list[DoctorCheck]:
    """Inspect selection, publication, registrations and actual resolver output."""
    callback_for(agent, 'sessionStart')
    checks = []
    try:
        with open_workspace(cwd, agent=agent, resolve_skills=False) as workspace:
            selected = any(item.ref == ZMEM for item in workspace.bundle.profiles)
            context = next((item for item in workspace.bundle.contexts if item.ref == ZMEM), None)
            trait = next((item for item in workspace.bundle.traits if item.ref == ZMEM), None)
            if selected and (context is None or trait is None):
                raise ConfigurationError('selected zmem profile lacks persistent or runtime policy')
            checks.append(DoctorCheck('guidance-selection', 'ok',
                'zmem lifecycle profile selected' if selected else 'zmem lifecycle profile not selected'))
            if context is not None:
                body = _plain(context.data['attach']['context'][0]['body'])
                checks.append(_persistent_check(workspace.consumer, body))
            else:
                checks.append(DoctorCheck('guidance-context', 'ok', 'standing memory context not selected'))
            runtime_body = _plain(trait.data['body']) if trait else None
    except (ConfigurationError, OSError, ValueError, KeyError, IndexError) as error:
        return [DoctorCheck('guidance-selection', 'failed', str(error)),
                DoctorCheck('guidance-host-receipt', 'warning', 'host receipt and agent adherence unverified')]
    checks.extend(_native_checks(agent))
    checks.extend(_generation_check(cwd, agent, event, runtime_body, inspect) for event in EVENTS)
    checks.append(DoctorCheck('guidance-host-receipt', 'warning',
        'host receipt and agent adherence unverified; generated output is not delivery evidence'))
    return checks

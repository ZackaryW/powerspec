"""Inspect and narrowly update committed consumer configuration."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import subprocess

import tomlkit

from .catalog import ConfigurationError, reference
from .consumer import discover_consumer
from .utils.atomic import AtomicWriteError, replace_bytes


@dataclass(frozen=True)
class ConfigurationResult:
    path: Path
    profile: str | None
    exclude_profiles: tuple[str, ...]
    variables: dict


@dataclass(frozen=True)
class ConfigurationUpdate:
    path: Path
    updated: bool
    profile: str | None


def _editor_argv(editor: str, *, windows: bool | None = None) -> list[str]:
    """Parse EDITOR while removing Windows-only grouping quotes."""
    windows = os.name == "nt" if windows is None else windows
    argv = shlex.split(editor, posix=not windows)
    if windows:
        argv = [
            item[1:-1]
            if len(item) >= 2 and item.startswith('"') and item.endswith('"')
            else item
            for item in argv
        ]
    return argv


def _consumer(cwd: Path):
    consumer = discover_consumer(Path(cwd), runtime=False)
    if consumer is None:
        raise ConfigurationError("no owning openspec/.pspec/config.toml within this Git repository")
    return consumer


def read_configuration(cwd: Path) -> ConfigurationResult:
    consumer = _consumer(cwd)
    return ConfigurationResult(
        consumer.config_path,
        consumer.config.profile,
        tuple(consumer.config.exclude_profiles),
        dict(consumer.config.vars),
    )


def set_profile(cwd: Path, profile: str | None) -> ConfigurationUpdate:
    if profile:
        reference(profile)
    consumer = _consumer(cwd)
    path = consumer.config_path
    try:
        original = path.read_bytes()
        document = tomlkit.parse(original.decode("utf-8-sig"))
        document["profile"] = profile or ""
        candidate = tomlkit.dumps(document).encode("utf-8")
        if path.read_bytes() != original:
            raise ConfigurationError("consumer configuration changed while updating profile; rerun the command")
        updated = replace_bytes(path, candidate)
    except AtomicWriteError as error:
        raise ConfigurationError(str(error)) from error
    except (OSError, ValueError) as error:
        if isinstance(error, ConfigurationError):
            raise
        raise ConfigurationError(f"{path}: {error}") from error
    return ConfigurationUpdate(path, updated, profile or None)


def edit_configuration(cwd: Path, *, environment=None) -> Path:
    consumer = _consumer(cwd)
    values = os.environ if environment is None else environment
    editor = values.get("VISUAL") or values.get("EDITOR")
    if not editor:
        raise ConfigurationError("set VISUAL or EDITOR before running config edit")
    argv = _editor_argv(editor)
    if not argv:
        raise ConfigurationError("VISUAL or EDITOR is empty")
    try:
        result = subprocess.run([*argv, str(consumer.config_path)], cwd=consumer.git_root)
    except (OSError, ValueError) as error:
        raise ConfigurationError(f"cannot launch editor: {error}") from error
    if result.returncode:
        raise ConfigurationError(f"editor exited {result.returncode}")
    return consumer.config_path

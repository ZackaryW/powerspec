"""Convert application results into stable serialization values."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
import json
from pathlib import Path
from types import MappingProxyType
from collections.abc import Mapping


def to_data(value):
    """Convert dataclasses and common immutable values to JSON-compatible data."""
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: to_data(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (Mapping, MappingProxyType)):
        return {str(key): to_data(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [to_data(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported result value: {type(value).__name__}")


def json_text(value) -> str:
    """Render exactly one compact JSON value."""
    return json.dumps(to_data(value), ensure_ascii=False, separators=(",", ":"), sort_keys=True)

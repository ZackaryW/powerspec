"""Workset default members, kept in a Powerspec-owned user file.

OpenSpec worksets have no default field and Powerspec never edits OpenSpec's
registry, so each entry stores the default label, its path, and a snapshot of
the workset's member paths. A snapshot that no longer matches makes the
default inert instead of pointing at the wrong project.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tomllib

import tomlkit

from .utils.atomic import replace_bytes
from .workset_openspec import Workset


class DefaultsError(ValueError):
    """The defaults file cannot be read as Powerspec workset defaults."""


@dataclass(frozen=True)
class WorksetDefault:
    label: str
    path: str
    members: tuple[str, ...]


def defaults_file() -> Path:
    return Path.home() / ".powerspec" / "worksets.toml"


def normalize(path) -> str:
    """One comparable spelling for OpenSpec, payload, and Git paths."""
    return os.path.normcase(os.path.normpath(os.path.abspath(str(path)))).replace("\\", "/")


def record_for(workset: Workset, label: str) -> WorksetDefault:
    selected = [member for member in workset.members if member.name == label]
    if not selected:
        labels = ", ".join(member.name for member in workset.members)
        raise ValueError(f"{label!r} is not a member of {workset.name}; members: {labels}")
    return WorksetDefault(label, Path(selected[0].path).as_posix(),
                          tuple(sorted(Path(member.path).as_posix() for member in workset.members)))


def load(path: Path) -> dict[str, WorksetDefault]:
    if not path.exists():
        return {}
    try:
        document = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise DefaultsError(f"cannot read workset defaults {path}: {error}") from error
    worksets = document.get("worksets", {})
    if not isinstance(worksets, dict):
        raise DefaultsError(f"workset defaults {path}: [worksets] must be a table")
    entries = {}
    for name, entry in worksets.items():
        members = entry.get("members") if isinstance(entry, dict) else None
        if (not isinstance(entry, dict) or not isinstance(entry.get("default"), str)
                or not isinstance(entry.get("path"), str) or not isinstance(members, list)
                or not all(isinstance(item, str) for item in members)):
            raise DefaultsError(f"workset defaults {path}: entry {name!r} needs default, path and members")
        entries[name] = WorksetDefault(entry["default"], entry["path"], tuple(members))
    return entries


def store(path: Path, entries: dict[str, WorksetDefault]) -> bool:
    """Atomically write *entries*; returns False when the file already matched."""
    document = tomlkit.document()
    table = tomlkit.table()
    for name in sorted(entries):
        entry = entries[name]
        item = tomlkit.table()
        item["default"] = entry.label
        item["path"] = entry.path
        item["members"] = list(entry.members)
        table[name] = item
    document["worksets"] = table
    path.parent.mkdir(parents=True, exist_ok=True)
    return replace_bytes(path, tomlkit.dumps(document).encode("utf-8"))


def staleness(entry: WorksetDefault, workset: Workset | None) -> str | None:
    """``None`` when *entry* still describes *workset*, otherwise the reason."""
    if workset is None:
        return "workset removed"
    if entry.label not in {member.name for member in workset.members}:
        return "label no longer a member"
    if {normalize(item) for item in entry.members} != {normalize(member.path) for member in workset.members}:
        return "members changed"
    return None


def match(entries: dict[str, WorksetDefault], paths) -> tuple[str | None, WorksetDefault | None, tuple[str, ...]]:
    """The one entry whose member snapshot equals *paths*, plus any ambiguous names."""
    wanted = {normalize(item) for item in paths}
    found = sorted(name for name, entry in entries.items()
                   if {normalize(item) for item in entry.members} == wanted)
    if len(found) == 1:
        return found[0], entries[found[0]], ()
    return None, None, tuple(found)


def default_workset(adapter, name: str, label: str | None = None, *, clear: bool = False,
                    path: Path | None = None) -> dict:
    """Show, set, or clear one workset's default, validating through OpenSpec."""
    if clear and label is not None:
        raise ValueError("--clear does not take a member label")
    path = path or defaults_file()
    entries = load(path)
    current = entries.get(name)
    result = {"ok": True, "workset": name, "default": None, "path": None, "status": None}
    if clear:
        if current is not None:
            del entries[name]
            store(path, entries)
        return {**result, "action": "cleared" if current is not None else "absent"}
    worksets = adapter.list_worksets()
    if label is not None:
        if name not in worksets:
            raise ValueError(f"Unknown OpenSpec workset: {name}")
        entry = record_for(worksets[name], label)
        action = "unchanged" if entry == current else "set"
        if action == "set":
            entries[name] = entry
            store(path, entries)
        current = entry
    else:
        action = "shown"
    if current is None:
        return {**result, "action": action}
    reason = staleness(current, worksets.get(name))
    return {**result, "action": action, "default": current.label, "path": current.path,
            "status": "current" if reason is None else f"stale: {reason}"}


def carry_default(source: Workset, output: Workset, *, path: Path | None = None) -> dict | None:
    """After a published launch, give the output the source's current default label."""
    path = path or defaults_file()
    entries = load(path)
    entry = entries.get(source.name)
    if entry is None:
        return None
    reason = staleness(entry, source)
    if reason is None and entry.label not in {member.name for member in output.members}:
        reason = "label not launched"
    if reason is not None:
        return {"action": "skipped", "reason": reason}
    carried = record_for(output, entry.label)
    existing = entries.get(output.name)
    if existing == carried:
        return {"action": "reused", "label": carried.label}
    if existing is not None:
        return {"action": "kept", "label": existing.label}
    entries[output.name] = carried
    store(path, entries)
    return {"action": "recorded", "label": carried.label}


def refresh_after_append(original: Workset, appended: Workset, *, path: Path | None = None) -> str | None:
    """Keep a current default's member snapshot in step with a verified append."""
    path = path or defaults_file()
    entries = load(path)
    entry = entries.get(original.name)
    if entry is None:
        return None
    reason = staleness(entry, original)
    if reason is not None:
        return f"stale: {reason}"
    entries[original.name] = record_for(appended, entry.label)
    store(path, entries)
    return "refreshed"

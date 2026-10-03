"""Change transfer with verified snapshots and private, resumable cleanup receipts."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath

from .utils.atomic import replace_bytes
from .utils.git_worktrees import inspect_repository
from .utils.tree_copy import TreeSnapshot, snapshot_tree, copy_verified_tree, assert_plain_path
from .workset_openspec import validate_name
from .workset_stores import RootPlan


def snapshot_data(snapshot):
    return [list(entry) for entry in snapshot.entries]


@dataclass(frozen=True)
class TransferPlan:
    root: RootPlan
    name: str
    source: Path
    destination: Path
    key: dict
    snapshot: TreeSnapshot
    receipt: dict | None


def receipt_path(root, key):
    digest = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()
    path = inspect_repository(root).git_dir / "powerspec/transfers" / (digest + ".json")
    assert_plain_path(path)
    return path


def read_receipt(root, key):
    path = receipt_path(root, key)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_bytes())
        if data["version"] != 1 or data["key"] != key or data["stage"] not in ("prepared", "copied", "published", "cleaning", "complete"):
            raise ValueError("receipt identity or stage mismatch")
        seen = set()
        for name, digest in data["snapshot"]:
            parts = PurePosixPath(name)
            if (not isinstance(name, str) or parts.is_absolute() or not parts.parts or
                any(part in (".", "..") for part in name.split("/")) or "\\" in name or ":" in name or name in seen):
                raise ValueError("invalid snapshot path")
            if digest is not None and (not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest)):
                raise ValueError("invalid snapshot digest")
            seen.add(name)
        return data
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError(f"Invalid transfer receipt at {path}: {error}") from error


def save_receipt(transfer, stage):
    path = receipt_path(transfer.root.destination, transfer.key)
    path.parent.mkdir(parents=True, exist_ok=True)
    replace_bytes(path, json.dumps({"version": 1, "key": transfer.key, "snapshot": snapshot_data(transfer.snapshot), "stage": stage}, sort_keys=True).encode())


def verify_change(adapter, root, name, identity=None, destination=None):
    result = adapter.change_status(root, name, identity)
    if Path(result.get("root", {}).get("path", "")).resolve() != root.resolve():
        raise ValueError(f"OpenSpec resolved a different planning root for {root}")
    expected = destination or root / "openspec/changes" / name
    if Path(result.get("changeRoot", "")).resolve() != expected.resolve():
        raise ValueError(f"OpenSpec resolved a different change: {expected}")


def projected_snapshot(view, relative):
    prefix = relative.as_posix().rstrip("/") + "/"
    entries = {}
    for name in view.names():
        if not name.startswith(prefix):
            continue
        short = name[len(prefix):]
        content = view.read(Path(name))
        entries[short] = hashlib.sha256(content).hexdigest()
        for parent in PurePosixPath(short).parents:
            if str(parent) != ".":
                entries[str(parent)] = None
    return TreeSnapshot(tuple(sorted(entries.items()))) if entries else None


def plan_transfer(adapter, plan, roots, views, name, store, keep_source):
    if not name:
        if store or keep_source:
            raise ValueError("--store and --keep-source require --change")
        return None
    validate_name(name)
    if store and not any(r.original_id == store for r in roots):
        raise ValueError(f"Source store is outside this workset: {store}")
    candidates = []
    for root in roots:
        if store and root.original_id != store:
            continue
        source = root.source / "openspec/changes" / name
        destination = root.destination / "openspec/changes" / name
        assert_plain_path(source)
        assert_plain_path(destination)
        key = {"source_workset": plan.source.name, "output_workset": plan.name,
               "source": str(source), "destination": str(destination), "mode": "copy" if keep_source else "move"}
        receipt = read_receipt(root.destination, key) if root.repository.reuse else None
        if not source.is_dir() and receipt is None:
            continue
        if receipt:
            snapshot = TreeSnapshot(tuple((n, d) for n, d in receipt["snapshot"]))
            if receipt["stage"] == "complete" and not keep_source:
                if source.exists():
                    raise ValueError(f"Source reappeared after a completed move: {source}")
                verify_change(adapter, root.destination, name, root.identity)
            elif receipt["stage"] == "cleaning":
                if source.exists():
                    remaining = dict(snapshot_tree(source).entries)
                    original = dict(snapshot.entries)
                    if any(n not in original or original[n] != d for n, d in remaining.items()):
                        raise ValueError(f"Source changed during interrupted cleanup: {source}")
            elif not source.is_dir() or snapshot_tree(source) != snapshot:
                raise ValueError(f"Source differs from transfer receipt: {source}")
        else:
            snapshot = snapshot_tree(source)
            # Explicit source IDs are only used when already registered.
            registered = adapter.list_stores()
            verify_change(adapter, root.source, name, root.original_id if root.original_id in registered else None)
        completed = receipt and receipt["stage"] == "complete"
        if not completed:
            if root.repository.reuse and destination.exists():
                existing = snapshot_tree(destination)
            else:
                view = views[root.repository.repository.common_dir]
                relative = destination.relative_to(root.repository.destination)
                existing = projected_snapshot(view, relative)
            if existing is not None and existing != snapshot:
                raise ValueError(f"Destination has different content: {destination}")
            if receipt and receipt["stage"] in ("copied", "published", "cleaning") and existing is None:
                raise ValueError(f"Verified transfer destination disappeared: {destination}")
        candidates.append(TransferPlan(root, name, source, destination, key, snapshot, receipt))
    if not candidates:
        raise ValueError(f"No active change {name!r} in this workset (archived changes are not eligible)")
    if len(candidates) != 1:
        owners = ", ".join(f"{c.root.original_id or '(unregistered local root)'}: {c.root.source}" for c in candidates)
        raise ValueError(f"Ambiguous change {name!r}; select its original --store ID. Candidates: {owners}")
    return candidates[0]


def copy_change(adapter, transfer, outcome=None):
    if transfer is None:
        return None
    outcome = outcome if outcome is not None else {"source": transfer.source, "destination": transfer.destination}
    receipt = transfer.receipt
    if receipt and receipt["stage"] == "complete":
        verify_change(adapter, transfer.root.destination, transfer.name, transfer.root.identity)
        outcome["action"] = "already-copied" if transfer.key["mode"] == "copy" else "already-moved"
        return outcome
    if not receipt:
        save_receipt(transfer, "prepared")
    outcome["receipt"] = receipt_path(transfer.root.destination, transfer.key)
    if not receipt or receipt["stage"] not in ("copied", "published", "cleaning"):
        copy_verified_tree(transfer.source, transfer.destination, transfer.snapshot)
        outcome["action"] = "copied-unverified"
        save_receipt(transfer, "copied")
    elif snapshot_tree(transfer.destination) != transfer.snapshot:
        raise ValueError("Destination changed before transfer completion")
    verify_change(adapter, transfer.root.destination, transfer.name, transfer.root.identity)
    outcome["action"] = "copied"
    return outcome


def finish_transfer(transfer, outcome):
    if transfer is None or (transfer.receipt and transfer.receipt["stage"] == "complete"):
        return
    if transfer.key["mode"] == "copy":
        save_receipt(transfer, "complete")
        return
    if snapshot_tree(transfer.destination) != transfer.snapshot:
        raise ValueError("Destination changed before source cleanup")
    expected = dict(transfer.snapshot.entries)
    remaining = dict(snapshot_tree(transfer.source).entries) if transfer.source.exists() else {}
    partial = transfer.receipt and transfer.receipt["stage"] == "cleaning"
    if (not partial and remaining != expected) or any(n not in expected or expected[n] != d for n, d in remaining.items()):
        raise ValueError("Source changed before cleanup; both copies preserved")
    save_receipt(transfer, "cleaning")
    # The whole-tree comparison above detects edits before cleanup; per-file
    # checks detect later changes. This does not promise a concurrent-writer lock.
    for name, digest in sorted(remaining.items(), key=lambda entry: (entry[0].count("/"), entry[0]), reverse=True):
        path = transfer.source / name
        assert_plain_path(path)
        if digest is None:
            path.rmdir()  # refuses newly added files
        else:
            with path.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if actual != digest:
                raise ValueError(f"Source changed during cleanup: {path}")
            path.unlink()
    if transfer.source.exists():
        transfer.source.rmdir()
    save_receipt(transfer, "complete")
    outcome["action"] = "moved"

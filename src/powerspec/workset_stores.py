"""Discover represented planning roots and route only spawned store identities."""
from dataclasses import dataclass
from io import StringIO
import os
from pathlib import Path

from ruamel.yaml import YAML

from .utils.atomic import replace_bytes
from .utils.git_worktrees import git_bytes, resolve_commit, inspect_repository
from .utils.tree_copy import assert_plain_path
from .worksets import branch_token, RepositoryPlan
from .workset_openspec import validate_name


def yaml_mapping(content: bytes, label: str):
    try:
        yaml = YAML()
        yaml.preserve_quotes = True
        data = yaml.load(content.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("expected a mapping")
        return yaml, data
    except Exception as error:
        raise ValueError(f"Invalid YAML at {label}: {error}") from error


def update_field(path: Path, key: str, expected: set, value: str) -> bool:
    assert_plain_path(path)
    yaml, data = yaml_mapping(path.read_bytes(), str(path))
    if data.get(key) not in expected:
        raise ValueError(f"Unexpected {key} at {path}: {data.get(key)!r}")
    if data.get(key) == value:
        return False
    data[key] = value
    stream = StringIO()
    yaml.dump(data, stream)
    return replace_bytes(path, stream.getvalue().encode("utf-8"))


def source_files(root: Path):
    """Walk without following links or nested repositories; no global discovery."""
    for directory, folders, files in os.walk(root, followlinks=False):
        base = Path(directory)
        folders[:] = [name for name in folders if name != ".git" and
                      not (base / name).is_symlink() and not (base / name).is_junction() and
                      not ((base / name) / ".git").exists()]
        for name in files:
            yield base / name


class TargetView:
    """Inspect the selected Git tree before creating a checkout, or a reused tree."""
    def __init__(self, item: RepositoryPlan):
        self.item = item
        self.entries = {}
        if item.reuse:
            return
        self.commit = item.base or resolve_commit(item.repository.root, "refs/heads/" + item.branch)
        raw = git_bytes(item.repository.root, "ls-tree", "-rz", "--full-tree", self.commit)
        for record in raw.split(b"\0"):
            if not record:
                continue
            header, name = record.split(b"\t", 1)
            mode, kind, oid = header.split()
            self.entries[os.fsdecode(name)] = (mode, kind, oid.decode("ascii"))

    def names(self):
        if self.item.reuse:
            return [p.relative_to(self.item.destination).as_posix() for p in source_files(self.item.destination)]
        return list(self.entries)

    def directory(self, relative: Path) -> bool:
        if self.item.reuse:
            path = self.item.destination / relative
            assert_plain_path(path)
            return path.is_dir()
        prefix = relative.as_posix().rstrip("/") + "/"
        return any(name.startswith(prefix) for name in self.entries)

    def read(self, relative: Path) -> bytes | None:
        if self.item.reuse:
            path = self.item.destination / relative
            assert_plain_path(path)
            return path.read_bytes() if path.exists() else None
        name = relative.as_posix()
        entry = self.entries.get(name)
        # A linked ancestor must not make an apparently missing resource valid.
        for parent in relative.parents:
            ancestor = self.entries.get(parent.as_posix())
            if ancestor and ancestor[0] not in (b"100644", b"100755"):
                raise ValueError(f"Unsupported Git path: {relative}")
        if entry is None:
            return None
        if entry[0] not in (b"100644", b"100755") or entry[1] != b"blob":
            raise ValueError(f"Unsupported Git path: {relative}")
        return git_bytes(self.item.repository.root, "--attr-source=" + self.commit,
                         "cat-file", "--filters", "--path=" + name, entry[2])


@dataclass(frozen=True)
class StorePlan:
    original_id: str
    identity: str
    source: Path
    destination: Path
    repository: RepositoryPlan


@dataclass(frozen=True)
class PointerPlan:
    path: Path
    original_id: str
    identity: str
    expected_root: Path


@dataclass(frozen=True)
class RootPlan:
    source: Path
    destination: Path
    original_id: str | None
    identity: str | None
    repository: RepositoryPlan


def plan_stores(adapter, plan):
    registered = adapter.list_stores()
    found = {}
    roots = {}
    views = {p.repository.common_dir: TargetView(p) for p in plan.repositories}
    for item in plan.repositories:
        source = item.repository.root
        for identity, root in registered.items():
            if root.is_relative_to(source):
                if inspect_repository(root).common_dir != item.repository.common_dir:
                    continue
                if root in found and found[root][0] != identity:
                    raise ValueError(f"Multiple identities for store root: {root}")
                found[root] = (identity, item)
        for path in source_files(source):
            if path.name == "store.yaml" and path.parent.name == ".openspec-store":
                assert_plain_path(path)
                _, metadata = yaml_mapping(path.read_bytes(), str(path))
                identity = metadata.get("id")
                validate_name(identity)
                root = path.parent.parent
                if root in found and found[root][0] != identity:
                    raise ValueError(f"Store metadata/registration identity mismatch at {root}")
                found[root] = (identity, item)
            if path.name == "config.yaml" and path.parent.name == "openspec":
                root = path.parent.parent
                if (path.parent / "changes").is_dir() or (path.parent / "specs").is_dir():
                    roots[root] = RootPlan(root, item.destination / root.relative_to(source), None, None, item)
        # Planning roots do not require config.yaml to exist.
        for directory, folders, _ in os.walk(source, followlinks=False):
            base = Path(directory)
            folders[:] = [f for f in folders if f != ".git" and not (base / f).is_symlink()
                          and not (base / f).is_junction() and not (base / f / ".git").exists()]
            if base.name == "openspec" and any(f in folders for f in ("changes", "specs")):
                root = base.parent
                roots.setdefault(root, RootPlan(root, item.destination / root.relative_to(source), None, None, item))
    stores = []
    ids = {}
    errors = []
    for root, (original_id, item) in found.items():
        try:
            if original_id in ids and ids[original_id] != root:
                raise ValueError(f"Duplicate represented store identity: {original_id}")
            ids[original_id] = root
            identity = f"{original_id}-{branch_token(item.branch)}"
            validate_name(identity)
            destination = item.destination / root.relative_to(item.repository.root)
            if identity in registered and registered[identity] != destination:
                raise ValueError(f"Store {identity} conflicts with registration at {registered[identity]}")
            view = views[item.repository.common_dir]
            relative = root.relative_to(item.repository.root)
            metadata = view.read(relative / ".openspec-store/store.yaml")
            if metadata is not None and yaml_mapping(metadata, str(destination))[1].get("id") not in (original_id, identity):
                raise ValueError(f"Unexpected spawned store identity at {destination}")
            if not view.directory(relative / "openspec/specs") or not view.directory(relative / "openspec/changes"):
                raise ValueError(f"Selected branch lacks a healthy store root at {destination}")
            stores.append(StorePlan(original_id, identity, root, destination, item))
            roots[root] = RootPlan(root, destination, original_id, identity, item)
        except (ValueError, OSError) as error:
            errors.append(str(error))
    if len({s.identity for s in stores}) != len(stores):
        errors.append("Generated store identities collide")
    mapping = {s.original_id: s for s in stores}
    mapped_ids = {s.identity: s for s in stores}
    pointers = []
    for item in plan.repositories:
        view = views[item.repository.common_dir]
        for name in view.names():
            relative = Path(name)
            if relative.name != "config.yaml" or relative.parent.name != "openspec":
                continue
            try:
                _, config = yaml_mapping(view.read(relative), name)
                current = config.get("store")
                source_path = item.repository.root / relative
                source_id = None
                if source_path.is_file():
                    assert_plain_path(source_path)
                    source_id = yaml_mapping(source_path.read_bytes(), str(source_path))[1].get("store")
                if current is not None and not isinstance(current, str):
                    raise ValueError(f"Invalid store pointer in {name}")
                if source_id is not None and not isinstance(source_id, str):
                    raise ValueError(f"Invalid source store pointer in {source_path}")
                if item.reuse and source_id in mapping and current not in (source_id, mapping[source_id].identity):
                    raise ValueError(f"Unexpected edited store pointer: {item.destination / relative}")
                selected = mapping.get(current) or mapped_ids.get(current)
                if selected:
                    own_root = item.destination / relative.parent.parent
                    local = view.directory(relative.parent / "changes") or view.directory(relative.parent / "specs")
                    pointers.append(PointerPlan(item.destination / relative, selected.original_id,
                                                selected.identity, own_root if local else selected.destination))
            except (ValueError, OSError) as error:
                errors.append(str(error))
    if errors:
        raise ValueError("Store preflight failed:\n" + "\n".join(errors))
    return tuple(stores), tuple(pointers), tuple(roots.values()), views


def prepare_stores(adapter, stores, pointers, effects):
    for store in stores:
        metadata = store.destination / ".openspec-store/store.yaml"
        assert_plain_path(metadata)
        if metadata.exists() and update_field(metadata, "id", {store.original_id, store.identity}, store.identity):
            effects.append({"action": "metadata-updated", "path": metadata})
        try:
            adapter.register_store(store.destination, store.identity)
        except (ValueError, OSError):
            # A CLI timeout/failure can follow a successful registry write.
            # Preserve and report observed registration without claiming success.
            observed = None
            try:
                observed = adapter.list_stores().get(store.identity)
            except (ValueError, OSError):
                pass
            effects.append({"action": "store-registration-failed", "id": store.identity,
                            "path": store.destination, "observed_root": observed})
            raise
        effects.append({"action": "store-registered", "id": store.identity, "path": store.destination})
    for pointer in pointers:
        if update_field(pointer.path, "store", {pointer.original_id, pointer.identity}, pointer.identity):
            effects.append({"action": "pointer-updated", "path": pointer.path})
        result = adapter.call("list", cwd=pointer.path.parent.parent)
        if Path(result.get("root", {}).get("path", "")).resolve() != pointer.expected_root.resolve():
            raise ValueError(f"OpenSpec resolved an unexpected root for {pointer.path}")

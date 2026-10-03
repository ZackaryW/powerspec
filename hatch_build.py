"""Hatch build hook for immutable upstream OpenSpec skill resources."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
from urllib.request import urlopen

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from zuu.case12 import GitHubSubpath, GitHubSubpathError


MANIFEST = "UPSTREAM_SNAPSHOT.json"
PROVENANCE = "UPSTREAM_PROVENANCE.md"
LICENSE = "UPSTREAM_LICENSE.txt"
OVERRIDE_ENV = "POWERSPEC_OPENSPEC_SOURCE"
NAME = re.compile(r"[a-z0-9][a-z0-9-]*")


class BuildSourceError(RuntimeError):
    """The declared build resource could not be reproduced safely."""


def _regular_files(root: Path):
    for path in sorted(root.rglob("*")):
        try:
            mode = path.lstat().st_mode
        except OSError as error:
            raise BuildSourceError(f"cannot inspect build source path: {path}") from error
        if stat.S_ISLNK(mode) or path.is_junction():
            raise BuildSourceError(f"build source contains a redirected path: {path}")
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise BuildSourceError(f"build source contains an unsupported path: {path}")
        yield path


def _copy_tree(source: Path, destination: Path) -> None:
    if not source.is_dir() or source.is_symlink() or source.is_junction():
        raise BuildSourceError(f"build source is not a regular directory: {source}")
    destination.mkdir(parents=True)
    for path in _regular_files(source):
        relative = path.relative_to(source)
        target = destination / relative
        if not target.resolve().is_relative_to(destination.resolve()):
            raise BuildSourceError(f"build source path escapes its destination: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())


def _skill_name(path: Path) -> str:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as error:
        raise BuildSourceError(f"cannot read skill entrypoint: {path}") from error
    if not lines or lines[0] != "---":
        raise BuildSourceError(f"missing skill frontmatter: {path}")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise BuildSourceError(f"unterminated skill frontmatter: {path}") from error
    declared = None
    for line in lines[1:end]:
        if line.startswith("name:"):
            declared = line.partition(":")[2].strip().strip("'\"")
            break
    if declared is None or NAME.fullmatch(declared) is None:
        raise BuildSourceError(f"invalid skill name in {path}")
    return declared


def _digests(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in _regular_files(root)
        if path.name != MANIFEST
    }


def _manifest(config: dict, root: Path) -> dict:
    return {
        "version": 1,
        "owner": config["owner"],
        "repository": config["repository"],
        "revision": config["revision"],
        "files": _digests(root),
    }


def _validate_declaration(config: dict) -> tuple[str, ...]:
    required = {"owner", "repository", "revision", "skills", "license"}
    missing = sorted(required - config.keys())
    if missing:
        raise BuildSourceError(f"OpenSpec build source is missing: {', '.join(missing)}")
    revision = config["revision"]
    if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise BuildSourceError("OpenSpec build revision must be a lowercase full commit SHA")
    skills = config["skills"]
    if (
        not isinstance(skills, list)
        or not skills
        or len(set(skills)) != len(skills)
        or any(not isinstance(item, str) or NAME.fullmatch(item) is None for item in skills)
    ):
        raise BuildSourceError("OpenSpec skills must be unique lowercase skill names")
    if config["license"] != "LICENSE":
        raise BuildSourceError("OpenSpec license path must be LICENSE")
    return tuple(skills)


def _fetch_license(config: dict) -> bytes:
    url = (
        f"https://raw.githubusercontent.com/{config['owner']}/{config['repository']}/"
        f"{config['revision']}/{config['license']}"
    )
    try:
        with urlopen(url, timeout=30) as response:
            return response.read()
    except OSError as error:
        raise BuildSourceError("could not acquire the pinned OpenSpec license") from error


def _acquire(config: dict, root: Path, destination: Path) -> None:
    skills = _validate_declaration(config)
    override = os.environ.get(OVERRIDE_ENV)
    if override:
        source_root = Path(override).resolve(strict=True)
        for name in skills:
            _copy_tree(source_root / "skills" / name, destination / "skills" / name)
        license_bytes = (source_root / config["license"]).read_bytes()
    else:
        fetched = root / "fetched-skills"
        pattern = r"^(?:" + "|".join(re.escape(name) for name in skills) + r")(?:/|$)"
        try:
            GitHubSubpath(
                config["owner"],
                config["repository"],
                "skills",
                commit=config["revision"],
                include=(pattern,),
            ).sync(fetched)
        except (GitHubSubpathError, OSError) as error:
            raise BuildSourceError("could not acquire pinned OpenSpec skills") from error
        for name in skills:
            _copy_tree(fetched / name, destination / "skills" / name)
        license_bytes = _fetch_license(config)
    (destination / "skills" / LICENSE).write_bytes(license_bytes)


def _validate_snapshot(config: dict, root: Path, *, carried: bool) -> None:
    skills = _validate_declaration(config)
    expected = set(skills)
    actual = {
        path.name for path in (root / "skills").iterdir()
        if path.is_dir() and not path.is_symlink()
    }
    if actual != expected:
        raise BuildSourceError(
            f"OpenSpec skill roots differ from declaration: expected {sorted(expected)}, got {sorted(actual)}"
        )
    for name in skills:
        entrypoint = root / "skills" / name / "SKILL.md"
        if _skill_name(entrypoint) != name:
            raise BuildSourceError(f"OpenSpec skill identity does not match its root: {name}")
    if not (root / "skills" / LICENSE).is_file():
        raise BuildSourceError("OpenSpec snapshot is missing its license")
    manifest_path = root / MANIFEST
    if carried:
        try:
            observed = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as error:
            raise BuildSourceError("carried OpenSpec snapshot manifest is invalid") from error
        expected_manifest = _manifest(config, root)
        if observed != expected_manifest:
            raise BuildSourceError("carried OpenSpec snapshot content does not match its manifest")


def prepare_snapshot(config: dict, root: Path, destination: Path) -> Path:
    """Create or validate the immutable snapshot consumed by a Hatch build."""
    carried = root / "powerspec_build" / "openspec"
    if carried.is_dir():
        _validate_snapshot(config, carried, carried=True)
        return carried
    destination.mkdir(parents=True)
    acquisition = destination.parent / f".{destination.name}-acquire"
    acquisition.mkdir()
    try:
        _acquire(config, acquisition, destination)
    finally:
        shutil.rmtree(acquisition, ignore_errors=True)
    provenance = (
        "# Generated OpenSpec skill snapshot\n\n"
        f"- Repository: https://github.com/{config['owner']}/{config['repository']}\n"
        f"- Commit: `{config['revision']}`\n"
        "- Materialized by the Powerspec Hatch build hook.\n"
    )
    (destination / "skills" / PROVENANCE).write_text(provenance, encoding="utf-8")
    _validate_snapshot(config, destination, carried=False)
    (destination / MANIFEST).write_text(
        json.dumps(_manifest(config, destination), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination


class CustomBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version, build_data):
        source = dict(self.config.get("source", {}))
        self._temporary = Path(tempfile.mkdtemp(prefix="powerspec-build-"))
        try:
            snapshot = prepare_snapshot(source, Path(self.root), self._temporary / "openspec")
            force_include = build_data.setdefault("force_include", {})
            if self.target_name == "sdist":
                force_include[str(snapshot)] = "powerspec_build/openspec"
            else:
                force_include[str(snapshot / "skills")] = "powerspec/_resources/catalog/skills"
        except Exception:
            shutil.rmtree(self._temporary, ignore_errors=True)
            raise

    def finalize(self, version, build_data, artifact_path):
        shutil.rmtree(getattr(self, "_temporary", ""), ignore_errors=True)


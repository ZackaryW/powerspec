"""Supported OpenSpec CLI boundary for worksets and represented stores."""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


@dataclass(frozen=True)
class Member:
    name: str
    path: Path


@dataclass(frozen=True)
class Workset:
    name: str
    members: tuple[Member, ...]
    tool: str | None = None


def validate_name(name: str) -> None:
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError(f"Invalid OpenSpec name: {name!r}")


class OpenSpec:
    def __init__(self, cwd: Path, *, env=None, timeout=60):
        self.cwd = cwd
        self.env = dict(os.environ if env is None else env)
        self.timeout = timeout

    def call(self, *args: str, cwd: Path | None = None) -> dict:
        executable = shutil.which("openspec", path=self.env.get("PATH"))
        if not executable:
            raise ValueError("OpenSpec is required; install its CLI before using worksets")
        try:
            process = subprocess.run([executable, *args, "--json"], cwd=cwd or self.cwd,
                                     env=self.env, capture_output=True, timeout=self.timeout, shell=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ValueError(f"OpenSpec could not complete {args}: {error}") from error
        if process.returncode:
            detail = (process.stderr or process.stdout).decode("utf-8", errors="replace").strip()
            raise ValueError(f"OpenSpec {' '.join(args)} failed: {detail}")
        try:
            data = json.loads(process.stdout)
        except ValueError as error:
            raise ValueError("OpenSpec returned malformed JSON") from error
        if not isinstance(data, dict):
            raise ValueError("OpenSpec must return a JSON object")
        return data

    def list_worksets(self) -> dict[str, Workset]:
        data = self.call("workset", "list")
        result = {}
        try:
            if not isinstance(data["worksets"], list):
                raise TypeError()
            for row in data["worksets"]:
                validate_name(row["name"])
                if not isinstance(row["members"], list) or not row["members"]:
                    raise TypeError()
                members = []
                for member in row["members"]:
                    if not isinstance(member["name"], str) or not isinstance(member["path"], str):
                        raise TypeError()
                    members.append(Member(member["name"], Path(member["path"]).resolve()))
                if len({m.name for m in members}) != len(members) or row["name"] in result:
                    raise ValueError("Duplicate workset or member names")
                if row.get("tool") is not None and not isinstance(row["tool"], str):
                    raise TypeError()
                result[row["name"]] = Workset(row["name"], tuple(members), row.get("tool"))
        except (KeyError, TypeError) as error:
            raise ValueError("Malformed OpenSpec workset listing") from error
        return result

    def publish(self, workset: Workset) -> str:
        validate_name(workset.name)
        existing = self.list_worksets().get(workset.name)
        if existing:
            if existing.members != workset.members:
                raise ValueError(f"Workset {workset.name} has conflicting membership")
            return "reused"
        args = ["workset", "create", workset.name]
        for member in workset.members:
            args += ["--member", f"{member.name}={member.path}"]
        if workset.tool:
            args += ["--tool", workset.tool]
        try:
            self.call(*args)
        except ValueError:
            raced = self.list_worksets().get(workset.name)
            if not raced or raced.members != workset.members:
                raise
            return "reused"
        saved = self.list_worksets().get(workset.name)
        if not saved or saved.members != workset.members:
            raise ValueError("OpenSpec did not save the expected membership")
        return "created"

    def list_stores(self) -> dict[str, Path]:
        data = self.call("store", "list")
        try:
            if not isinstance(data["stores"], list):
                raise TypeError()
            result = {}
            for row in data["stores"]:
                validate_name(row["id"])
                if not isinstance(row["root"], str) or row["id"] in result:
                    raise TypeError()
                result[row["id"]] = Path(row["root"]).resolve()
            return result
        except (KeyError, TypeError) as error:
            raise ValueError("Malformed OpenSpec store listing") from error

    def register_store(self, root: Path, identity: str) -> None:
        prior = self.list_stores().get(identity)
        if prior is not None and prior != root.resolve():
            raise ValueError(f"Store {identity} is already registered at {prior}")
        self.call("store", "register", str(root), "--id", identity, "--yes")
        if self.list_stores().get(identity) != root.resolve():
            raise ValueError(f"Store registration verification failed: {identity}")

    def change_status(self, root: Path, name: str, store: str | None = None) -> dict:
        args = ["status", "--change", name]
        if store:
            args += ["--store", store]
        return self.call(*args, cwd=root)

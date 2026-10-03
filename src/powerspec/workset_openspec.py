"""Supported OpenSpec CLI boundary for worksets and represented stores."""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from .presentation import json_text


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
        command = [executable]
        if os.name == "nt" and Path(executable).suffix.lower() in (".cmd", ".bat"):
            # npm's batch shim passes through cmd.exe even with shell=False.
            # Invoke the public CLI entrypoint through Node so paths remain literal.
            directory = Path(executable).resolve().parent
            entry = directory / "node_modules/@fission-ai/openspec/bin/openspec.js"
            node = directory / "node.exe"
            runtime = str(node) if node.is_file() else shutil.which("node", path=self.env.get("PATH"))
            if not entry.is_file() or not runtime:
                raise ValueError("Cannot safely invoke this OpenSpec batch shim; install its npm CLI with Node on PATH")
            command = [runtime, str(entry)]
        try:
            process = subprocess.run([*command, *args, "--json"], cwd=cwd or self.cwd,
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
                    if (not member["name"] or member["name"] in (".", "..") or
                        any(c in member["name"] for c in "/\\") or not Path(member["path"]).is_absolute()):
                        raise ValueError("Invalid OpenSpec member label/path")
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
                if not isinstance(row["root"], str) or not Path(row["root"]).is_absolute() or row["id"] in result:
                    raise TypeError()
                result[row["id"]] = Path(row["root"]).resolve()
            return result
        except (KeyError, TypeError) as error:
            raise ValueError("Malformed OpenSpec store listing") from error

    def append_member(self, original: Workset, member: Member) -> str:
        """Replace a saved definition through OpenSpec; restore it on failure.

        The remove/create pair is not atomic. Never remove a definition observed
        after the initial removal, since another writer may have created it.
        """
        if self.list_worksets().get(original.name) != original:
            raise ValueError(f"Workset {original.name} changed before append; retry with its current definition")
        updated = Workset(original.name, (*original.members, member), original.tool)
        try:
            self.call("workset", "remove", original.name, "--yes")
            self.publish(updated)
            if self.list_worksets().get(original.name) != updated:
                raise ValueError("Recreated workset does not match the intended members and tool")
            return "appended"
        except (ValueError, OSError) as error:
            definition = f"Original definition: {json_text(original)}"
            try:
                observed = self.list_worksets().get(original.name)
            except (ValueError, OSError) as inspection_error:
                raise ValueError(f"Append failed: {error}. Cannot inspect recovery state: {inspection_error}. {definition}") from error
            if observed == updated:
                return "appended"  # Creation completed despite a lost response.
            if observed == original:
                raise ValueError(f"Append failed; original workset preserved: {error}") from error
            if observed is not None:
                raise ValueError(f"Append failed; a different workset now uses {original.name}; left untouched. {definition}") from error
            try:
                self.publish(original)
                if self.list_worksets().get(original.name) != original:
                    raise ValueError("Restored definition could not be verified")
            except (ValueError, OSError) as recovery_error:
                raise ValueError(f"Append failed: {error}. Could not restore original workset: {recovery_error}. {definition}") from error
            raise ValueError(f"Append failed; original workset restored: {error}") from error

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

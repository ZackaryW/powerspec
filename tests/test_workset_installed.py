"""Installed CLI evidence; every OpenSpec registry is confined to tmp_path."""
import json
import os
from pathlib import Path
import subprocess
import sysconfig

from test_workset_helpers import git, repo
from test_workset_transfer import planning_root, change, commit, adapter


def cli(args, cwd):
    executable = Path(sysconfig.get_path("scripts")) / ("pspec.exe" if os.name == "nt" else "pspec")
    result = subprocess.run([str(executable), "workset", *args, "--json"], cwd=cwd,
                            capture_output=True, text=True, timeout=90)
    payload = json.loads(result.stdout)
    return result, payload


def test_installed_multirepo_move_copy_and_retry(tmp_path, adapter):
    from powerspec.workset_openspec import Workset, Member
    first = repo(tmp_path / "first repo & literal")
    second = repo(tmp_path / "second")
    nested = first / "planning"
    planning_root(nested)
    planning_root(second)
    adapter.register_store(nested, "plans")
    adapter.register_store(second, "server")
    (first / "openspec").mkdir()
    (first / "openspec/config.yaml").write_text("store: plans\n")
    for root in (first, second):
        commit(root)
        git(root, "update-ref", "refs/remotes/origin/base", "HEAD")
    selected, untouched = change(nested), change(second)
    (first / "unrelated.txt").write_text("unrelated work")
    (nested / "openspec/.pspec").mkdir()
    (nested / "openspec/.pspec/current.toml").write_text('[vars]\nprivate = true\n')
    adapter.publish(Workset("source", (Member("app", first), Member("server", second))))
    ambiguous, rejected = cli(["launch", "source", "--branch", "feature/run", "--change", "feature"], tmp_path)
    assert ambiguous.returncode == 1 and "Ambiguous" in rejected["errors"][0]
    args = ["launch", "source", "--branch", "feature/run", "--repo7=server", "--branch7=backend",
            "--remote7=origin/base", "--change", "feature", "--store", "plans"]
    process, result = cli(args, tmp_path)
    assert process.returncode == 0, (process.stderr, result)
    assert process.stderr == ""
    assert result["workspace_ready"] and result["transfer"]["action"] == "moved"
    assert result["opening_command"] == "openspec workset open source-feature-run --tool code"
    assert not selected.exists() and untouched.is_dir()
    assert not (Path(result["members"][0]["path"]) / "unrelated.txt").exists()
    assert not (Path(result["members"][0]["path"]) / "planning/openspec/.pspec/current.toml").exists()
    assert {s["id"] for s in result["stores"]} == {"plans-feature-run", "server-backend"}
    assert [m["branch"] for m in result["members"]] == ["feature/run", "backend"]
    assert all(m.path not in (first, second) for m in adapter.list_worksets()["source-feature-run"].members)
    assert git(first, "branch", "--show-current") == "main"
    assert git(second, "branch", "--show-current") == "main"
    repeat, repeated = cli(args, tmp_path)
    assert repeat.returncode == 0 and repeated["transfer"]["action"] == "already-moved", repeated
    copied_source = change(nested, "copy-task")
    copied, copy_result = cli(["launch", "source", "--branch", "copy", "--change", "copy-task", "--keep-source"], tmp_path)
    assert copied.returncode == 0, copy_result
    assert copied_source.is_dir() and copy_result["transfer"]["action"] == "copied"
    assert adapter.list_stores()["plans"] == nested
    assert adapter.list_stores()["server"] == second


def test_installed_add_and_usage_output(tmp_path, adapter):
    source = repo(tmp_path / "repo")
    process, result = cli(["add", "demo", "--path", str(source)], tmp_path)
    assert process.returncode == 0 and result["action"] == "created"
    again, repeated = cli(["add", "demo", "--path", str(source)], tmp_path)
    assert again.returncode == 0 and repeated["action"] == "reused"
    missing, error = cli(["launch", "demo"], tmp_path)
    assert missing.returncode == 2 and error["stage"] == "arguments"

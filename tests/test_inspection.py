import subprocess

import pytest

from powerspec.utils.inspection import inspect_executable, semantic_version


def test_semantic_version_accepts_two_or_three_components_and_rejects_other_text():
    assert semantic_version("git version 2.50") == "2.50"
    assert semantic_version("OpenSpec 1.13.2") == "1.13.2"
    try:
        semantic_version("development build")
    except ValueError as error:
        assert "semantic version" in str(error)
    else:
        raise AssertionError("missing semantic version must fail")


def test_inspect_executable_reports_parsed_success(tmp_path, monkeypatch):
    import powerspec.utils.inspection as inspection

    monkeypatch.setattr(inspection.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(
        inspection.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "tool 2.4.1\n", ""),
    )
    result = inspect_executable(
        ["tool", "--version"], cwd=tmp_path, timeout=2, parse_version=lambda value: value.split()[-1]
    )
    assert result.ok and result.executable == "/bin/tool"
    assert result.version == "2.4.1" and result.kind == "ok"


def test_inspect_executable_distinguishes_missing_exit_timeout_and_parse(tmp_path, monkeypatch):
    import powerspec.utils.inspection as inspection

    monkeypatch.setattr(inspection.shutil, "which", lambda name: None)
    assert inspect_executable(["missing"], cwd=tmp_path, timeout=1).kind == "missing"

    monkeypatch.setattr(inspection.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(
        inspection.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 3, "", "broken"),
    )
    failed = inspect_executable(["tool"], cwd=tmp_path, timeout=1)
    assert failed.kind == "exit" and failed.returncode == 3 and failed.stderr == "broken"

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(inspection.subprocess, "run", timeout)
    assert inspect_executable(["tool"], cwd=tmp_path, timeout=1).kind == "timeout"

    monkeypatch.setattr(
        inspection.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "unknown", ""),
    )

    def bad_version(value):
        raise ValueError("no version")

    assert inspect_executable(
        ["tool"], cwd=tmp_path, timeout=1, parse_version=bad_version
    ).kind == "version"


def test_inspect_explicit_staged_binary_without_path_extension_lookup(tmp_path, monkeypatch):
    import powerspec.utils.inspection as inspection

    staged = tmp_path / "manager.stage"
    staged.write_bytes(b"staged executable")
    monkeypatch.setattr(inspection.shutil, "which", lambda name: None)
    calls = []

    def run(command, **options):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "tool 1.2.3\n", "")

    monkeypatch.setattr(inspection.subprocess, "run", run)
    result = inspect_executable([str(staged), "--version"], cwd=tmp_path, timeout=2)
    assert result.ok
    assert calls == [[str(staged), "--version"]]


def test_inspect_relative_path_resolves_from_requested_cwd(tmp_path, monkeypatch):
    import powerspec.utils.inspection as inspection

    staged = tmp_path / "manager.stage"
    staged.write_bytes(b"staged executable")
    monkeypatch.setattr(inspection.shutil, "which", lambda name: None)
    calls = []

    def run(command, **options):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "ok", "")

    monkeypatch.setattr(inspection.subprocess, "run", run)
    assert inspect_executable(["./manager.stage"], cwd=tmp_path, timeout=2).ok
    assert calls == [[str(staged)]]


def test_missing_explicit_path_does_not_fall_back_to_path(tmp_path, monkeypatch):
    import powerspec.utils.inspection as inspection

    monkeypatch.setattr(inspection.shutil, "which", lambda name: "/unrelated/tool.exe")
    monkeypatch.setattr(inspection.subprocess, "run", lambda *a, **k: pytest.fail("launched missing path"))
    assert inspect_executable([str(tmp_path / "missing.stage")], cwd=tmp_path, timeout=2).kind == "missing"

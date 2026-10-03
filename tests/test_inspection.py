import subprocess

from powerspec.utils.inspection import inspect_executable


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

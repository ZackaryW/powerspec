import os
import sys
import pytest
from powerspec.utils.processes import ProcessJSONError, run_json_object


def invoke(tmp_path, code, *args, timeout=5):
    return run_json_object([sys.executable, "-c", code, *args], cwd=tmp_path,
                           env={**os.environ, "HELPER_VALUE": "fixture"}, timeout=timeout)


def test_process_environment_cwd_and_literal_arguments(tmp_path):
    value = invoke(tmp_path, "import json,os,sys; print(json.dumps(dict(cwd=os.getcwd(), value=os.environ['HELPER_VALUE'], arg=sys.argv[1], ok=False)))", "$(literal); & echo")
    assert value == {"cwd": str(tmp_path), "value": "fixture", "arg": "$(literal); & echo", "ok": False}
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("code,kind", [("raise SystemExit(3)", "exit"), ("print('invalid')", "json"), ("import sys; sys.stdout.buffer.write(bytes([255]))", "json"), ("print('[]')", "object"), ("print('null')", "object"), ("import time; time.sleep(10)", "timeout")])
def test_process_failures(tmp_path, code, kind):
    with pytest.raises(ProcessJSONError) as caught:
        invoke(tmp_path, code, timeout=0.1 if kind == "timeout" else 5)
    assert caught.value.kind == kind


@pytest.mark.parametrize("argv", [[], "echo {}", [3], [""], ["bad\x00name"]])
def test_bad_argv(tmp_path, argv):
    with pytest.raises(ProcessJSONError) as caught:
        run_json_object(argv, cwd=tmp_path, env=os.environ, timeout=5)
    assert caught.value.kind == "arguments"


def test_launch_failure(tmp_path):
    with pytest.raises(ProcessJSONError) as caught:
        run_json_object([str(tmp_path / "missing-program")], cwd=tmp_path, env=os.environ, timeout=5)
    assert caught.value.kind == "launch"

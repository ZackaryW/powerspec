"""Read one JSON object from real pipes without waiting for end of input."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest

from powerspec.utils.stdin_payload import read_json_object

SRC = str(Path(__file__).resolve().parents[1] / "src")
CHILD = ("import json, sys; from powerspec.utils.stdin_payload import read_json_object; "
         "print(json.dumps(read_json_object(sys.stdin, float(sys.argv[1]))), flush=True)")


def child(budget=0.5):
    env = dict(os.environ, PYTHONPATH=SRC)
    return subprocess.Popen([sys.executable, "-c", CHILD, str(budget)], env=env, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def finish(process, limit=5):
    """Wait without closing stdin (that would hide a reader waiting for EOF)."""
    started = time.monotonic()
    output = []
    drain = threading.Thread(target=lambda: output.append(process.stdout.read()), daemon=True)
    drain.start()
    try:
        process.wait(timeout=limit)
        drain.join(limit)
        assert not process.stdin.closed
        assert process.returncode == 0, process.stderr.read().decode()
        return json.loads(output[0].decode()), time.monotonic() - started
    finally:
        if process.poll() is None:
            process.kill()
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()


def test_complete_object_returns_while_the_pipe_stays_open():
    process = child(budget=3)
    process.stdin.write(b'{"workspacePaths": ["/work/app"]}')
    process.stdin.flush()

    value, elapsed = finish(process)

    assert value == {"workspacePaths": ["/work/app"]} and elapsed < 2.5


def test_object_split_across_writes_is_assembled():
    process = child(budget=3)
    process.stdin.write(b'{"a": "x')
    process.stdin.flush()
    time.sleep(0.2)
    process.stdin.write(b'y", "b": [1, 2]}\n')
    process.stdin.flush()

    assert finish(process)[0] == {"a": "xy", "b": [1, 2]}


def test_silent_open_pipe_gives_up_within_the_budget():
    process = child(budget=0.5)

    value, elapsed = finish(process)

    assert value is None and elapsed < 3


@pytest.mark.parametrize("payload", [b"not json", b"[1, 2]", b'"text"', b"", b'{"broken": '])
def test_unusable_input_is_none(payload):
    process = child(budget=0.5)
    process.stdin.write(payload)
    process.stdin.flush()

    assert finish(process)[0] is None


def test_large_object_arriving_in_chunks_is_read():
    process = child(budget=3)
    payload = json.dumps({"workspacePaths": ["/p" * 20000], "pad": "x" * 200000}).encode()
    for start in range(0, len(payload), 4096):
        process.stdin.write(payload[start:start + 4096])
        process.stdin.flush()

    value = finish(process)[0]

    assert value["pad"] == "x" * 200000


def test_terminal_is_not_read():
    class Terminal:
        def isatty(self):
            return True

        def read(self, *args):
            raise AssertionError("terminal input must not be read")

    assert read_json_object(Terminal(), 0.5) is None


def test_in_memory_streams_are_supported():
    import io

    assert read_json_object(io.StringIO('{"a": 1}'), 0.5) == {"a": 1}


def test_end_of_input_without_an_object_returns_promptly():
    process = child(budget=3)
    process.stdin.write(b'{"partial": ')
    process.stdin.close()
    started = time.monotonic()
    try:
        process.wait(timeout=5)
        assert json.loads(process.stdout.read().decode()) is None
        assert time.monotonic() - started < 2.5
    finally:
        process.stdout.close()
        process.stderr.close()

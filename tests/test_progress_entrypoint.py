"""Real CLI entrypoint streams observed before a controlled operation finishes."""
import queue
import subprocess
import sys
import threading

import pytest


HARNESS = r'''
from contextlib import contextmanager
from functools import partial
import importlib
from pathlib import Path
import sys
from types import SimpleNamespace
from powerspec.cli import main
from powerspec.catalog import ConfigurationError
from powerspec.progress import lifecycle_progress, stage
from powerspec.provisioning import ProvisionResult, HookOutcome
from powerspec.upgrading import UpgradeResult

command, fail = sys.argv[1:]
module = importlib.import_module('powerspec.cli.' + command)
module.lifecycle_progress = partial(lifecycle_progress, interval=.05)
def blocked(*args, **kwargs):
    with stage('Preparing source: blocked (main)'):
        sys.stdin.readline()
        if fail == 'true':
            raise ConfigurationError('source blocked: timeout; mutation may have committed; receipt retained')
    if command == 'init':
        return SimpleNamespace(ok=True, provisioning=ProvisionResult(()), hooks=HookOutcome('codex', 'reused'))
    return UpgradeResult('success')
if command == 'init':
    module.plan_initialization = lambda *a, **k: SimpleNamespace(profile=None)
    module.initialize = lambda *a, **k: SimpleNamespace(root=Path.cwd(), warnings=())
    module.install_consumer = blocked
else:
    module.discover_consumer = lambda *a, **k: SimpleNamespace(config_path=Path.cwd() / 'config.toml')
    @contextmanager
    def catalog():
        yield Path.cwd()
    module.builtin_catalog_root = catalog
    module.SaucepanSources = lambda **k: object()
    module.upgrade_consumer = blocked
sys.argv = ['pspec', command, '--agent', 'codex']
main()
'''


def run_blocked_cli(python, command, failure, *, cwd):
    process = subprocess.Popen([str(python), '-c', HARNESS, command, str(failure).lower()],
        cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    messages = queue.Queue()
    stderr = []
    def read():
        for line in process.stderr:
            stderr.append(line)
            messages.put(line)
        messages.put(None)
    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    try:
        while True:
            line = messages.get(timeout=10)
            assert line is not None, ''.join(stderr)
            if 'Waiting: Preparing source: blocked' in line:
                break
        assert process.poll() is None, ''.join(stderr)
        process.stdin.write('\n')
        process.stdin.flush()
        process.stdin.close()
        process.wait(timeout=15)
        reader.join(timeout=2)
        assert not reader.is_alive()
        return process.returncode, process.stdout.read(), ''.join(stderr)
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        reader.join(timeout=2)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None:
                stream.close()


@pytest.mark.parametrize('command', ['init', 'upgrade'])
@pytest.mark.parametrize('failure', [False, True])
def test_progress_arrives_before_command_completes(tmp_path, command, failure):
    code, stdout, stderr = run_blocked_cli(sys.executable, command, failure, cwd=tmp_path)
    assert code == int(failure), stderr
    assert 'Starting: Preparing source: blocked' in stderr
    assert 'Waiting:' not in stdout and 'Starting:' not in stdout
    assert 'Waiting:' in stderr and 'no completion reported' in stderr
    if failure:
        assert 'failed: Preparing source: blocked' in stderr
        assert 'timeout; mutation may have committed; receipt retained' in stderr
        assert 'complete.' not in stdout
    else:
        assert 'done: Preparing source: blocked' in stderr
        assert 'complete.' in stdout
    terminal = max(stderr.rfind('done: Preparing source'), stderr.rfind('failed: Preparing source'))
    assert 'Waiting: Preparing source' not in stderr[terminal:]

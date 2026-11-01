"""The milkpan protocol client against a stub executable."""
import json
import os
from pathlib import Path
import sys

import pytest

from powerspec.milkpan_client import Milkpan, MilkpanError, MilkpanUnavailable

STUB = r'''
import json, sys, time
args = sys.argv[1:]
if args == ["--version"]:
    print("milkpan 0.2.0"); sys.exit(0)
assert args[:6] == ["--home", HOME, "--format", "json", "--protocol", "1"], args
command = args[6:]
if command == ["protocol"]:
    print(json.dumps({"protocol": 1, "ok": True, "result": {"protocol": 1, "supported": [1]}}))
elif command[:1] == ["acquire"]:
    print(json.dumps({"protocol": 1, "ok": True, "result": {"lease": {"id": "L1", "spec": command[1]}, "path": "/x", "fetched": True}}))
elif command[:1] == ["release"]:
    print(json.dumps({"protocol": 1, "ok": False, "error": {"code": "not_found", "message": "no live lease", "details": {"lease": command[1]}}}), file=sys.stderr)
    sys.exit(1)
elif command[:1] == ["sleep"]:
    time.sleep(5)
else:
    print("not json"); sys.exit(3)
'''


@pytest.fixture
def stub(tmp_path):
    script = tmp_path / 'stub.py'
    script.write_text(f'HOME = {str(tmp_path / "home")!r}\n' + STUB, encoding='utf-8')
    if os.name == 'nt':
        launcher = tmp_path / 'milkpan.cmd'
        launcher.write_text(f'@"{sys.executable}" "{script}" %*\r\n', encoding='utf-8')
    else:
        launcher = tmp_path / 'milkpan'
        launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding='utf-8')
        launcher.chmod(0o755)
    return Milkpan(launcher, tmp_path / 'home', timeout=30)


def test_success_envelopes_return_results(stub):
    assert stub.protocol()['supported'] == [1]
    acquired = stub.acquire('github:octo/tools@main', scope='consumer-1')
    assert acquired['lease']['spec'] == 'github:octo/tools@main' and acquired['fetched']
    assert stub.version() == '0.2.0'


def test_error_envelopes_on_stderr_raise_with_code_and_details(stub):
    with pytest.raises(MilkpanError) as raised:
        stub.release('L9')
    assert raised.value.code == 'not_found' and raised.value.details == {'lease': 'L9'}


def test_output_outside_the_protocol_is_unavailable(stub):
    with pytest.raises(MilkpanUnavailable):
        stub.result('unknown')


def test_timeouts_and_missing_executables_are_unavailable(stub, tmp_path):
    with pytest.raises(MilkpanUnavailable):
        stub.with_timeout(0.5).result('sleep')
    with pytest.raises(MilkpanUnavailable):
        Milkpan(tmp_path / 'missing-milkpan', tmp_path).protocol()

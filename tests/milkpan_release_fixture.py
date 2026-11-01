"""A loopback stand-in for milkpan's GitHub releases, built around a real milkpan.

The executable comes from `MILKPAN_TEST_BINARY`, else `POWERSPEC_MILKPAN`,
else a sibling `../milkpan` build. Tests skip when none exists.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import http.server
import io
import json
import os
from pathlib import Path
import tarfile
import threading
import zipfile

import pytest

from powerspec.milkpan_binary import Release, executable_name


def milkpan_binary() -> Path:
    for variable in ('MILKPAN_TEST_BINARY', 'POWERSPEC_MILKPAN'):
        if os.environ.get(variable):
            return Path(os.environ[variable])
    sibling = Path(__file__).resolve().parents[2] / 'milkpan' / 'target'
    for profile in ('release', 'debug'):
        candidate = sibling / profile / executable_name()
        if candidate.is_file():
            return candidate
    pytest.skip('no milkpan executable: set MILKPAN_TEST_BINARY')


def release_archive(tag: str, target: str, binary: bytes) -> tuple[str, bytes]:
    folder = f'milkpan-{tag}-{target}'
    if 'windows' in target:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as bundle:
            bundle.writestr(f'{folder}/milkpan.exe', binary)
            bundle.writestr(f'{folder}/README.md', 'milkpan')
        return f'{folder}.zip', buffer.getvalue()
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as bundle:
        info = tarfile.TarInfo(f'{folder}/milkpan')
        info.size, info.mode = len(binary), 0o755
        bundle.addfile(info, io.BytesIO(binary))
    return f'{folder}.tar.gz', buffer.getvalue()


@contextmanager
def release_server(tags: list[str], target: str):
    """Serve `tags` of a fake milkpan release; yields (Release factory, request log)."""
    binary = milkpan_binary().read_bytes()
    assets, by_id, requests = {}, {}, []
    for index, tag in enumerate(tags):
        name, data = release_archive(tag, target, binary)
        assets[tag] = (name, data)
        by_id[100 + index] = data

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            requests.append(self.path)
            body, status = b'{}', 404
            for index, tag in enumerate(tags):
                name, data = assets[tag]
                if self.path == f'/download/{tag}/{name}':
                    body, status = data, 200
                elif self.path == f'/repos/zackaryw/milkpan/releases/tags/{tag}':
                    body, status = json.dumps({'assets': [{'id': 100 + index, 'name': name}]}).encode(), 200
                elif self.path == f'/repos/zackaryw/milkpan/releases/assets/{100 + index}':
                    body, status = data, 200
            self.send_response(status)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_address[1]}'

    def release(tag: str) -> Release:
        name, data = assets[tag]
        return Release(tag=tag, digests={name: hashlib.sha256(data).hexdigest()},
                       download_base=f'{base}/download', github_api=base,
                       env={'GH_TOKEN': '', 'GITHUB_TOKEN': ''})

    try:
        yield release, requests
    finally:
        server.shutdown()

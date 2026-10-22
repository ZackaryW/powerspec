"""Loopback fixture serving unmodified published Saucepan artifacts."""
from contextlib import contextmanager
from dataclasses import replace
import hashlib
import http.server
import json
from pathlib import Path
import platform
import threading

from powerspec.saucepan_provider import PROVIDER


@contextmanager
def released_provider(directory):
    directory = Path(directory)
    target = {('Windows', 'AMD64'): 'x86_64-pc-windows-msvc',
              ('Windows', 'ARM64'): 'aarch64-pc-windows-msvc',
              ('Linux', 'x86_64'): 'x86_64-unknown-linux-musl',
              ('Darwin', 'arm64'): 'aarch64-apple-darwin',
              ('Darwin', 'x86_64'): 'x86_64-apple-darwin'}[(platform.system(), platform.machine())]
    archive = f'saucepan-{PROVIDER.tag}-{target}.zip'
    payload = (directory / archive).read_bytes()
    requests = []
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            if self.path.startswith('/repos/'):
                data = json.dumps(dict(id=1, tag_name=PROVIDER.tag, draft=False, prerelease=False,
                    assets=[dict(id=1, name=archive, browser_download_url=base + '/archive',
                                 digest='sha256:' + hashlib.sha256(payload).hexdigest())])).encode()
            elif self.path == '/archive':
                data = payload
            elif self.path.startswith(f'/releases/{PROVIDER.tag}/'):
                name = self.path.rsplit('/', 1)[-1]
                if name not in {'install.ps1', 'install.sh', 'SHA256SUMS', archive}:
                    self.send_error(404)
                    return
                data = (directory / name).read_bytes()
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        def log_message(self, *_):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    base = f'http://127.0.0.1:{server.server_port}'
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield replace(PROVIDER, release_base=base + '/releases', fixture_api=base), requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

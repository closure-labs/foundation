#!/usr/bin/env python3
"""Exercise real Nix resume recovery using loopback HTTP and a temporary store."""
import argparse
import hashlib
import http.server
import importlib.util
import json
import os
import platform
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import time

DATA = b'finite-nix-transport-fixture\n' * 100000


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('home_download_fixture', Path(__file__).resolve().parents[1] / 'scripts/home.py')
    home = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(home)
    requests = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            request = {'range': self.headers.get('Range'), 'path': self.path}
            requests.append(request)
            if request['range']:
                request['status'] = 416
                self.send_response(416)
                self.send_header('Content-Range', f'bytes */{len(DATA)}')
                self.end_headers()
                return
            self.send_response(200)
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Length', str(len(DATA)))
            self.end_headers()
            body = DATA[:len(DATA) // 2] if len(requests) == 1 else DATA
            request.update(status=200, bytesSent=len(body))
            self.wfile.write(body)
            self.wfile.flush()
            if len(requests) == 1:
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()

        def log_message(self, *_args):
            pass

    with http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with tempfile.TemporaryDirectory(prefix='foundation-download-') as temporary:
                command = ['nix', '--extra-experimental-features', 'nix-command', 'store', 'prefetch-file',
                           '--store', 'local?root=' + temporary, '--json', f'http://127.0.0.1:{server.server_port}/fixture']
                trials = []
                for attempt in (1, 2):
                    started = time.monotonic()
                    result = subprocess.run(command, text=True, capture_output=True, timeout=30)
                    trials.append({'attempt': attempt, 'seconds': time.monotonic() - started,
                                   'status': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
                original_requests = list(requests)
                requests.clear()
                started = time.monotonic()
                recovered = home.capture_build(command)
                recovery = {'seconds': time.monotonic() - started, 'result': json.loads(recovered), 'requests': list(requests)}
                assert trials[0]['status'] == 1 and 'HTTP error 416' in trials[0]['stderr']
                assert trials[1]['status'] == 0
                assert recovery['result']['hash'] == json.loads(trials[1]['stdout'])['hash']
                assert recovery['result']['hash'] == 'sha256-8zv2LrrsyWqTFy1OcKSGbiawxc4vLUXE8nCWH2BlBa0='
                assert [r['range'] for r in recovery['requests']] == [None, 'bytes=1450000-', None]
                revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=Path(__file__).resolve().parents[1], text=True).strip()
                report = {'schema': 1, 'kind': 'nix-interrupted-download-fixture', 'repository': 'closure-labs/foundation',
                          'sourceRevision': os.environ.get('GITHUB_SHA', revision),
                          'workingHelperSha256': hashlib.sha256(Path(home.__file__).read_bytes()).hexdigest(),
                          'runner': {'system': platform.system(), 'machine': platform.machine()},
                          'authorizesPublication': False, 'nixVersion': subprocess.check_output(['nix', '--version'], text=True).strip(),
                          'command': command[:-1] + ['loopback fixture URL'], 'bodySha256': hashlib.sha256(DATA).hexdigest(),
                          'bodyBytes': len(DATA), 'requests': original_requests, 'trials': trials, 'recovery': recovery}
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(report, indent=2) + '\n')
                print(json.dumps(report, indent=2))
        finally:
            server.shutdown()


if __name__ == '__main__':
    main()

"""Small non-authoritative observations with fixed schemas and no command data."""
import contextlib
import datetime
import json
import math
import os
import subprocess
import sys
import time


def emit(stage, seconds, status=0, details=None, started_at=None):
    if os.environ.get('FOUNDATION_TIMINGS') != '1':
        return
    try:
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 0 <= seconds <= 86400:
            return
        value = {'schema': 1 if details is None else 2, 'kind': 'foundation-stage-timing',
                 'authorizesPublication': False, 'stage': stage, 'seconds': round(seconds, 6),
                 'startedAt': started_at or datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'outcome': 'success' if status == 0 else 'error', 'status': status}
        if details is not None:
            value['details'] = details
        raw = 'FOUNDATION_TIMING ' + json.dumps(value, separators=(',', ':'))
        if len(raw.encode()) <= 1023:
            print(raw, file=sys.stderr, flush=True)
    except (OSError, ValueError, TypeError):
        pass


@contextlib.contextmanager
def timing(stage):
    if os.environ.get('FOUNDATION_TIMINGS') != '1':
        yield
        return
    try:
        started = time.monotonic()
        at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    except (OSError, ValueError):
        yield
        return
    status = None
    try:
        yield
        status = 0
    except subprocess.CalledProcessError as error:
        status = error.returncode
        raise
    finally:
        try:
            emit(stage, time.monotonic() - started, status, started_at=at)
        except (OSError, ValueError):
            pass


class NixActivities:
    """Nix internal-json start/stop activity IDs; fields/text are never retained.

    105 is actBuild and 108 actSubstitute in Nix's versioned logging interface.
    The logger has no evaluation activity boundary. Missing stops remain unknown.
    """
    TYPES = {105: 'build', 108: 'substitution'}

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.pending, self.intervals = {}, {'build': [], 'substitution': []}
        self.counts = {'build': 0, 'substitution': 0}
        self.buffer = b''
        self.rejected, self.incomplete = 0, False
        self.enabled = os.environ.get('FOUNDATION_TIMINGS') == '1'

    def feed(self, chunk):
        if not self.enabled:
            return
        try:
            for line in (self.buffer + chunk).splitlines(keepends=True):
                if not line.endswith(b'\n'):
                    self.buffer = line if len(line) <= 8192 else b''
                    if len(line) > 8192:
                        self.incomplete = True
                    continue
                self.buffer = b''
                if not line.startswith(b'@nix '):
                    continue
                if len(line) > 8192:
                    self.rejected = min(1000000, self.rejected + 1)
                    continue
                try:
                    value = json.loads(line[5:])
                    action, identity = value.get('action'), value.get('id')
                    if type(identity) is not int or identity < 0:
                        continue
                    now = self.clock()
                    if not math.isfinite(now):
                        self.incomplete = True
                        continue
                    if action == 'start' and value.get('type') in self.TYPES:
                        if identity in self.pending or sum(self.counts.values()) >= 4096:
                            self.incomplete = True
                            continue
                        kind = self.TYPES[value['type']]
                        self.pending[identity] = (kind, now)
                        self.counts[kind] += 1
                    elif action == 'stop' and identity in self.pending:
                        kind, start = self.pending.pop(identity)
                        if now < start or now - start > 86400:
                            self.incomplete = True
                        else:
                            self.intervals[kind].append((start, now))
                except (ValueError, TypeError, AttributeError):
                    self.rejected = min(1000000, self.rejected + 1)
        except (OSError, ValueError, TypeError):
            self.incomplete = True

    @staticmethod
    def union(intervals):
        merged = []
        for start, end in sorted(intervals):
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
            else:
                merged.append((start, end))
        return merged

    def finish(self):
        if not self.enabled:
            return
        build = self.union(self.intervals['build'])
        substitute = self.union(self.intervals['substitution'])
        incomplete = self.incomplete or bool(self.pending) or bool(self.buffer) or bool(self.rejected)
        overlap = sum(max(0, min(b, d) - max(a, c)) for a, b in build for c, d in substitute)
        # Unknown coverage cannot become zero work or an exact evaluation split.
        known = sum(self.counts.values()) > 0 and not incomplete
        emit('nix-activities', 0, details={
            'logger': 'nix-internal-json-v1', 'evaluation': 'unknown',
            'builds': self.counts['build'], 'substitutions': self.counts['substitution'],
            'buildSeconds': round(sum(b-a for a,b in build), 6) if known else None,
            'substitutionSeconds': round(sum(b-a for a,b in substitute), 6) if known else None,
            'overlapSeconds': round(overlap, 6) if known else None,
            'incomplete': incomplete, 'rejectedRecords': self.rejected})


class Resources:
    """Separate observed client scope and shared root daemon cgroups (cgroup v2)."""
    def __init__(self, root=None):
        from pathlib import Path
        self.root = root or Path('/sys/fs/cgroup')
        self.values = {}
        self.next_sample = 0
        self.enabled = os.environ.get('FOUNDATION_TIMINGS') == '1'

    def sample(self, pid):
        if not self.enabled:
            return
        try:
            now = time.monotonic()
            if now < self.next_sample:
                return
            self.next_sample = now + 1
            from pathlib import Path
            paths = {'resource-nix-daemon': self.root / 'system.slice/nix-daemon.service',
                     'resource-determinate-daemon': self.root / 'system.slice/determinate-nixd.service'}
            pending, seen = [pid], set()
            while pending and len(seen) < 32:
                current = pending.pop()
                if current in seen:
                    continue
                seen.add(current)
                try:
                    group = Path(f'/proc/{current}/cgroup').read_text()[:4096].splitlines()
                    for line in group:
                        if (line.startswith('0::') and line.endswith('.scope')
                                and line.rsplit('/', 1)[-1].startswith('foundation-realisation-')):
                            relative = line[3:].lstrip('/')
                            if '..' not in relative.split('/'):
                                paths['resource-client'] = self.root / relative
                    children = Path(f'/proc/{current}/task/{current}/children').read_text()[:4096]
                    pending.extend(int(child) for child in children.split()[:32] if child.isdigit())
                except (OSError, ValueError):
                    pass
            for stage, path in paths.items():
                row = self.values.setdefault(stage, {})
                for name, filename in (('memoryCurrentBytes', 'memory.current'), ('memoryPeakBytes', 'memory.peak')):
                    try:
                        text = path.joinpath(filename).read_text()[:128].strip()
                        value = int(text)
                        if 0 <= value <= 2**63 - 1:
                            row[name] = max(row.get(name, 0), value)
                    except (OSError, ValueError):
                        pass
                try:
                    lines = path.joinpath('cpu.stat').read_text()[:4096].splitlines()
                    for line in lines:
                        if line.startswith('usage_usec '):
                            value = int(line.split()[1])
                            if 0 <= value <= 2**63 - 1:
                                row.setdefault('cpuStart', value)
                                row['cpuEnd'] = value
                except (OSError, ValueError, IndexError):
                    pass
        except (OSError, ValueError):
            pass

    def finish(self):
        if not self.enabled:
            return
        for stage in ('resource-client', 'resource-nix-daemon', 'resource-determinate-daemon'):
            row = self.values.get(stage, {})
            cpu = row.get('cpuEnd', 0) - row.get('cpuStart', 0)
            emit(stage, 0, details={'scope': 'client' if stage == 'resource-client' else 'shared-daemon',
                'memoryCurrentBytes': row.get('memoryCurrentBytes'), 'memoryPeakBytes': row.get('memoryPeakBytes'),
                'cpuUsageUsec': cpu if 'cpuEnd' in row and cpu >= 0 else None,
                'available': bool(row)})


@contextlib.contextmanager
def activation_observations():
    """Pass an opt-in marker to the actual user service, then join its receipt."""
    from pathlib import Path
    import secrets
    marker = receipt = None
    if os.environ.get('FOUNDATION_TIMINGS') == '1':
        try:
            runtime = Path(os.environ['XDG_RUNTIME_DIR'])
            if runtime.is_dir() and runtime.stat().st_uid == os.getuid():
                candidate = runtime / 'foundation-observation.env'
                receipt_candidate = runtime / 'foundation-flatpak-observation.json'
                if not receipt_candidate.exists() and not receipt_candidate.is_symlink():
                    nonce = secrets.token_hex(16)
                    descriptor = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    with os.fdopen(descriptor, 'w') as stream:
                        stream.write('FOUNDATION_TIMINGS=1\nFOUNDATION_OBSERVATION_NONCE=' + nonce + '\n')
                    marker, receipt = candidate, receipt_candidate
                    activation_started = time.monotonic()
        except (KeyError, OSError, ValueError):
            pass
    try:
        yield
    finally:
        if marker is not None:
            try:
                if receipt.is_file() and not receipt.is_symlink() and receipt.stat().st_size <= 1024:
                    value = json.loads(receipt.read_text())
                    if (set(value) == {'nonce', 'seconds', 'status'} and value['nonce'] == nonce
                            and type(value['status']) is int and -255 <= value['status'] <= 255):
                        emit('flatpak-work', value['seconds'], value['status'])
                        # Native monotonic unit timestamps observe the actual
                        # oneshot job, rather than activation-hook log arrival.
                        result = subprocess.run(['systemctl', '--user', 'show', 'flatpak-managed-install.service',
                            '-p', 'ExecMainStartTimestampMonotonic', '-p', 'ExecMainExitTimestampMonotonic',
                            '-p', 'ExecMainStatus'], capture_output=True, text=True, timeout=5, check=False)
                        if result.returncode == 0 and len(result.stdout) <= 4096:
                            fields = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
                            start = int(fields['ExecMainStartTimestampMonotonic']) / 1000000
                            end = int(fields['ExecMainExitTimestampMonotonic']) / 1000000
                            status = int(fields['ExecMainStatus'])
                            if activation_started <= start <= end <= time.monotonic() and status == value['status']:
                                emit('service-startup', end - start, status)
            except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
                pass
            finally:
                for path in (marker, receipt):
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        pass

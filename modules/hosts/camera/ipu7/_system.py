"""Install the current IPU7 WirePlumber policy system-wide. No legacy repair."""
import argparse
import fcntl
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

TARGET = Path('/etc/wireplumber/wireplumber.conf.d/50-foundation-ipu7.conf')
RECORD = TARGET.with_suffix('.sha256')
POLICY = Path(__file__).with_name('_policy.conf')
LOCK = Path('/run/lock/foundation-ipu7-system.lock')
MARKER = b'# Managed by Foundation IPU7 system policy.\n'


def detected():
    return any(
        any((Path('/sys/bus/pci/drivers') / driver).glob('????:??:??.?'))
        for driver in ('intel-ipu7', 'ipu7'))


def trusted(path, directory=False):
    info = path.lstat()
    return (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)) and info.st_uid == 0 and not info.st_mode & 0o022


def paths(create=False):
    for parent in list(reversed(TARGET.parent.parents)) + [TARGET.parent]:
        if create and not parent.exists():
            parent.mkdir(mode=0o755)
        if not trusted(parent, directory=True):
            raise RuntimeError(f'Refusing unsafe policy directory: {parent}')
    for path in (TARGET, RECORD):
        if path.exists() or path.is_symlink():
            if not trusted(path):
                raise RuntimeError('Refusing unsafe system policy file')


def installed():
    try:
        paths()
        content = TARGET.read_bytes()
        return content == POLICY.read_bytes() and RECORD.read_text() == hashlib.sha256(content).hexdigest()
    except (OSError, RuntimeError):
        return False


def write(path, content):
    fd, name = tempfile.mkstemp(prefix='.foundation-ipu7-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fchmod(stream.fileno(), 0o644)
            os.fchown(stream.fileno(), 0, 0)
            os.fsync(stream.fileno())
        os.replace(name, path)
        subprocess.run(['/usr/sbin/restorecon', '-F', str(path)], check=True)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def apply(action):
    paths(create=action == 'install')
    before = TARGET.read_bytes() if TARGET.exists() else None
    previous_hash = RECORD.read_text() if RECORD.exists() else None
    desired = POLICY.read_bytes()
    if not desired.startswith(MARKER):
        raise RuntimeError('Invalid packaged IPU7 policy')
    if before is not None and before != desired and (
        not before.startswith(MARKER) or previous_hash != hashlib.sha256(before).hexdigest()
    ):
        raise RuntimeError('Preserving custom or externally edited policy; reconcile it first')
    if action == 'uninstall':
        if before is not None:
            TARGET.unlink()
        if RECORD.exists():
            RECORD.unlink()
        print('Removed Foundation system-wide IPU7 policy.')
        return
    # Invalidate the public record before mutation. A failed operation cannot
    # suppress a subsequent privileged retry through a stale success record.
    if RECORD.exists():
        RECORD.unlink()
    try:
        write(TARGET, desired)
        write(RECORD, hashlib.sha256(desired).hexdigest().encode())
    except BaseException:
        if RECORD.exists():
            RECORD.unlink()
        if before is None:
            if TARGET.exists():
                TARGET.unlink()
        else:
            write(TARGET, before)
        raise
    print('Installed system-wide IPU7 policy. Restart WirePlumber when audio can be interrupted.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'uninstall'))
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.action == 'install' and not detected():
        print('Skipping system IPU7 policy: no bound IPU7 controller.')
        return
    if args.dry_run:
        print(f'Dry run: would {args.action} system IPU7 policy; no sudo or writes.')
        return
    if args.action == 'install' and installed():
        print('System-wide IPU7 policy already matches; skipping sudo.')
        return
    if os.geteuid() != 0:
        print(f'Foundation IPU7: {args.action} shared camera policy for all users.\n'
              'Administrator access is required to manage /etc/wireplumber/wireplumber.conf.d/50-foundation-ipu7.conf.\n'
              'The OS continues to own drivers and IPA binaries. No legacy migration or service restart will run.', flush=True)
        subprocess.run(['/usr/bin/sudo', '--', sys.executable, '-I', str(Path(__file__).resolve()), args.action], check=True)
        return
    fd = os.open(LOCK, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        apply(args.action)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f'IPU7 system policy failed: {error}', file=sys.stderr)
        sys.exit(1)

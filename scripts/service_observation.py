"""Observe the actual Flatpak oneshot without changing its command or exit status."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from foundation_observations import emit


def main():
    # EnvironmentFile is absent outside an opted-in Foundation activation.
    enabled = os.environ.get('FOUNDATION_TIMINGS') == '1'
    nonce = os.environ.get('FOUNDATION_OBSERVATION_NONCE', '')
    started = time.monotonic() if enabled else None
    result = subprocess.run(sys.argv[1:], check=False)
    if enabled and len(nonce) == 32 and all(c in '0123456789abcdef' for c in nonce):
        elapsed = time.monotonic() - started
        try:
            runtime = Path(os.environ['XDG_RUNTIME_DIR'])
            # A fixed private receipt contains no executable path or arguments.
            record = {'nonce': nonce, 'seconds': elapsed, 'status': result.returncode}
            destination = runtime / 'foundation-flatpak-observation.json'
            descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, 'w') as stream:
                json.dump(record, stream)
        except (OSError, KeyError, ValueError):
            pass
        emit('flatpak-work', elapsed, result.returncode)
    if result.returncode < 0:
        import signal
        if -result.returncode not in (signal.SIGKILL, signal.SIGSTOP):
            signal.signal(-result.returncode, signal.SIG_DFL)
        os.kill(os.getpid(), -result.returncode)
    return result.returncode


if __name__ == '__main__': sys.exit(main())

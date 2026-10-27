"""Ensure the inherited stock CLI bundle; root setup remains Bluefin's service."""
import hashlib
import os
from pathlib import Path
import subprocess
import time

from foundation_observations import timing, emit

BREW = Path('/home/linuxbrew/.linuxbrew/bin/brew')
BREWFILE = Path('/usr/share/ublue-os/homebrew/cli.Brewfile')


def prepare(brew=BREW, brewfile=BREWFILE, run=subprocess.run, sleep=time.sleep,
            preinstall=Path('/usr/bin/brew-preinstall')):
    # Read only the immutable image's bundle, never a policy copied by Foundation.
    with timing('bluefin-readiness'):
        if not brewfile.is_file() or brewfile.is_symlink():
            raise ValueError('Inherited Bluefin CLI Brewfile is unavailable')
        identity = hashlib.sha256(brewfile.read_bytes()).hexdigest()
        # Bluefin's privileged brew-setup.service seeds /home/linuxbrew. Wait for
        # it rather than reproducing extraction/chown or starting a root service.
        for _ in range(120):
            if brew.is_file() and os.access(brew, os.X_OK):
                break
            sleep(1)
        else:
            raise ValueError('Bluefin brew-setup.service has not supplied Homebrew')
        env = dict(os.environ, HOMEBREW_NO_AUTO_UPDATE='1')
        cache = run([str(brew), '--cache'], env=env, text=True, capture_output=True, check=True).stdout.strip()
        cache_state = 'present' if cache and Path(cache).is_dir() else 'absent'
        emit('bluefin-bundle', 0, details={'brewfileSha256': identity, 'cache': cache_state,
                                         'closurePinned': False})
        ready = run([str(brew), 'bundle', 'check', '--file=' + str(brewfile)], env=env, check=False).returncode
        if ready not in (0, 1):
            raise subprocess.CalledProcessError(ready, ['brew', 'bundle', 'check'])
    with timing('bluefin-stock-install'):
        # The inherited user setup owns its stock preinstall bundles and state.
        # Do not reproduce its taps, removals or optional-bundle selection here.
        if preinstall.is_file():
            # Default blocking start joins an already running oneshot instead
            # of racing the upstream graphical-session setup. Do not use
            # --wait: upstream intentionally has RemainAfterExit=true.
            run(['systemctl', '--user', 'start', 'brew-preinstall.service'], env=env, check=True)
        if ready:
            run([str(brew), 'bundle', 'install', '--no-upgrade', '--file=' + str(brewfile)], env=env, check=True)
    with timing('bluefin-postcheck'):
        if hashlib.sha256(brewfile.read_bytes()).hexdigest() != identity:
            raise ValueError('Inherited Brewfile changed during preparation')
        run([str(brew), 'bundle', 'check', '--file=' + str(brewfile)], env=env, check=True)
        # Finite's config-only Fzf integration requires the upstream binary.
        if brew == BREW:
            run([str(brew), 'list', '--formula', 'fzf'], env=env, check=True)


if __name__ == '__main__':
    prepare()

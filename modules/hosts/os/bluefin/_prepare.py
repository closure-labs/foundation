"""Wait for Bluefin-owned default provisioning; never install optional bundles."""
import os
from pathlib import Path
import subprocess
import time

from foundation_observations import timing

BREW = Path('/home/linuxbrew/.linuxbrew/bin/brew')
PREINSTALL = Path('/usr/bin/brew-preinstall')
SERVICE = 'brew-preinstall.service'
DEFAULTS = Path('/usr/share/ublue-os/homebrew/preinstall.d')
FZF = (Path('/usr/bin/fzf'), BREW.parent / 'fzf')


def prepare(brew=BREW, run=subprocess.run, sleep=time.sleep, preinstall=PREINSTALL, fzf_paths=FZF, preinstall_dir=DEFAULTS):
    with timing('bluefin-readiness'):
        # Bluefin owns the root seed and user package policy. Older verified
        # images seed Homebrew only; newer images also ship user preinstall.
        has_preinstall = preinstall.exists() or preinstall.is_symlink()
        if has_preinstall and (not preinstall.is_file() or not os.access(preinstall, os.X_OK)):
            raise ValueError('Inherited Bluefin brew-preinstall is not executable')
        if has_preinstall:
            user = os.environ.get('USER', '')
            if user == 'gdm' or user.startswith('gdm-') or os.environ.get('HOME', '').startswith('/run/gdm/home/'):
                raise ValueError('Bluefin defaults require a real user session')
            bundles = list(preinstall_dir.glob('*.Brewfile')) if preinstall_dir.is_dir() else []
            if not bundles or any(not path.is_file() or not os.access(path, os.R_OK) for path in bundles):
                raise ValueError('Inherited Bluefin default manifests are unavailable')
        for _ in range(120):
            if brew.is_file() and os.access(brew, os.X_OK):
                break
            sleep(1)
        else:
            raise ValueError('Bluefin brew-setup.service has not supplied Homebrew')
    with timing('bluefin-stock-install'):
        # Blocking start joins an already-running oneshot. Upstream owns all
        # default manifests, trust decisions, inventory and package lifecycle.
        # Never start the executable directly or select optional cli.Brewfile.
        if has_preinstall:
            run(['systemctl', '--user', 'start', SERVICE], check=True, timeout=600)
    with timing('bluefin-postcheck'):
        command = ['systemctl', '--user', 'show', SERVICE] if has_preinstall else [
            'systemctl', 'show', 'brew-setup.service']
        command += ['--property=LoadState,ActiveState,SubState,Result,ExecMainStatus,ConditionResult']
        deadline = time.monotonic() + 120
        for _ in range(120):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ValueError('Bluefin default provisioning did not finish in time')
            result = run(command, check=True, text=True, capture_output=True, timeout=min(30, remaining))
            fields = {}
            for line in result.stdout.splitlines():
                key, separator, value = line.partition('=')
                if not separator or key in fields:
                    raise ValueError('Invalid Bluefin provisioning service state')
                fields[key] = value
            if not has_preinstall and fields.get('ActiveState') in ('activating', 'deactivating'):
                sleep(1)
                continue
            expected = {'LoadState': 'loaded', 'ActiveState': 'active', 'SubState': 'exited',
                        'Result': 'success', 'ExecMainStatus': '0', 'ConditionResult': 'yes'}
            if not has_preinstall:
                # Exact older Bluefin seed is a oneshot without RemainAfterExit;
                # seeded homes intentionally skip its path conditions on reboot.
                expected.update(ActiveState='inactive', SubState='dead',
                                ConditionResult=fields.get('ConditionResult'))
                if expected['ConditionResult'] not in ('yes', 'no'):
                    raise ValueError('Invalid Bluefin seed condition state')
            if fields != expected:
                raise ValueError('Bluefin default provisioning did not complete successfully')
            break
        else:
            raise ValueError('Bluefin default provisioning did not finish in time')
        # Config-only Fzf integration depends on the OS-owned binary. Test the
        # actual executable, not a package inventory or an optional Brewfile.
        if not any(path.is_file() and os.access(path, os.X_OK) for path in fzf_paths):
            raise ValueError('Bluefin default provisioning did not supply executable fzf')


if __name__ == '__main__':
    prepare()

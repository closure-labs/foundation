"""Check the host IPU7 IPA ABI without capture; repair only the known stale override."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

MARKER = '# Managed by Foundation IPU7 camera repair.\n'
LEGACY = '/var/lib/finite/libcamera/ipa'


def detected(sysfs=Path('/sys/bus/pci/drivers')):
    return any(re.fullmatch(r'[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]', p.name)
               for driver in ('intel-ipu7', 'ipu7')
               for p in (sysfs / driver).glob('*'))


def probe(module_path=None):
    # Use the OS binary and libraries. A Nix libcamera would test another ABI.
    env = dict(os.environ)
    for key in ('LIBCAMERA_IPA_MODULE_PATH', 'LD_LIBRARY_PATH', 'LD_PRELOAD'):
        env.pop(key, None)
    if module_path:
        env['LIBCAMERA_IPA_MODULE_PATH'] = str(module_path)
    result = subprocess.run(['/usr/bin/cam', '-c', '1', '--info'], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, timeout=15, check=False)
    return result.returncode, result.stdout


def usable(result):
    code, output = result
    return code == 0 and 'Pixelformat:' in output and not any(
        error in output for error in ('undefined symbol:', 'IPA init failed', 'Failed to create software ISP'))


def check(*, repair=False, sysfs=Path('/sys/bus/pci/drivers'),
          config=Path('/etc/libcamera/configuration.yaml'),
          candidates=(Path('/usr/lib64/libcamera/ipa'), Path('/usr/lib/libcamera/ipa')),
          user_config=None, run_probe=probe):
    if not detected(sysfs):
        return {'status': 'not-applicable', 'message': 'No bound Intel IPU7 controller detected.'}, 0
    baseline = run_probe()
    if usable(baseline):
        return {'status': 'ok', 'message': 'IPU7 camera formats enumerate with host libcamera. Capture has not been tested.'}, 0
    output = baseline[1]
    if not (config.exists() and LEGACY in config.read_text() and LEGACY in output
            and 'undefined symbol:' in output and 'IPA init failed' in output):
        return {'status': 'unresolved', 'message': 'IPU7 camera format enumeration failed; no known safe repair matches.',
                'details': output[-6000:]}, 1
    for candidate in candidates:
        if not (candidate / 'ipa_soft_simple.so').is_file():
            continue
        if not usable(run_probe(candidate)):
            continue
        root = user_config or Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config')))
        dropin = root / 'systemd/user/wireplumber.service.d/70-foundation-ipu7.conf'
        desired = MARKER + '[Service]\nEnvironment=LIBCAMERA_IPA_MODULE_PATH=' + str(candidate) + '\n'
        if dropin.is_symlink() or (dropin.exists() and dropin.read_text() != desired):
            return {'status': 'conflict', 'message': f'Preserving existing override: {dropin}'}, 1
        configured = dropin.exists()
        if repair and not configured:
            dropin.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation: never clobber a concurrent user edit.
            with dropin.open('x') as stream:
                stream.write(desired)
        return {'status': 'configured' if configured or repair else 'repair-available',
                'message': 'Stale IPA ABI override detected; matching host IPA restores formats. '
                           + ('Per-user override is configured. If not already applied to the running service, reload systemd and restart WirePlumber when audio interruption is acceptable, then reload Firefox.'
                              if configured or repair else 'Run foundation home camera --repair to configure the verified override.'),
                'override': str(dropin), 'modulePath': str(candidate)}, 0 if configured or repair else 1
    return {'status': 'unresolved', 'message': 'Stale IPU7 IPA module found, but host IPA did not restore formats. No files changed.'}, 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, prog='foundation home camera')
    parser.add_argument('--repair', action='store_true', help='Write a verified per-user override; never restart services')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    try:
        result, code = check(repair=args.repair)
    except (OSError, subprocess.TimeoutExpired) as error:
        result, code = {'status': 'unavailable', 'message': f'Camera check unavailable: {error}'}, 1
    print(json.dumps(result) if args.json else result['message'])
    raise SystemExit(code)


if __name__ == '__main__':
    main()

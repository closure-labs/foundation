"""Check the OS-owned IPU7 camera stack without capture or configuration changes."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess


def detected(sysfs=Path('/sys/bus/pci/drivers')):
    return any(re.fullmatch(r'[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]', p.name)
               for driver in ('intel-ipu7', 'ipu7')
               for p in (sysfs / driver).glob('*'))


def probe():
    # Test the host defaults, never another libcamera ABI or a per-user workaround.
    env = dict(os.environ)
    for key in ('LIBCAMERA_IPA_MODULE_PATH', 'LD_LIBRARY_PATH', 'LD_PRELOAD'):
        env.pop(key, None)
    result = subprocess.run(['/usr/bin/cam', '-c', '1', '--info'], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, timeout=15, check=False)
    return result.returncode, result.stdout


def usable(result):
    code, output = result
    return code == 0 and 'Pixelformat:' in output and not any(
        error in output for error in ('undefined symbol:', 'IPA init failed', 'Failed to create software ISP'))


def check(*, sysfs=Path('/sys/bus/pci/drivers'), run_probe=probe):
    if not detected(sysfs):
        return {'status': 'not-applicable', 'message': 'No bound Intel IPU7 controller detected.'}, 0
    result = run_probe()
    if usable(result):
        return {'status': 'ok', 'message': 'IPU7 camera formats enumerate with the OS-owned stack. Capture has not been tested.'}, 0
    return {'status': 'unresolved', 'message': 'IPU7 camera format enumeration failed; no configuration was changed.',
            'details': result[1][-6000:]}, 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, prog='foundation home camera')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    try:
        result, code = check()
    except (OSError, subprocess.TimeoutExpired) as error:
        result, code = {'status': 'unavailable', 'message': f'Camera check unavailable: {error}'}, 1
    print(json.dumps(result) if args.json else result['message'])
    raise SystemExit(code)


if __name__ == '__main__':
    main()

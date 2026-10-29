import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('ipu7', Path(__file__).resolve().parents[1] / 'modules/hosts/camera/ipu7/_check.py')
ipu7 = importlib.util.module_from_spec(SPEC)
sys.dont_write_bytecode = True
SPEC.loader.exec_module(ipu7)
GOOD = (0, 'Available cameras:\nPixelformat: XRGB8888\n')
BAD = (0, 'undefined symbol: foo\nIPA init failed\n')


class CameraTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.drivers = Path(self.temp.name) / 'drivers'
        self.device = self.drivers / 'intel-ipu7/0000:00:05.0'
        self.device.mkdir(parents=True)

    def test_no_controller_never_probes(self):
        self.device.rmdir()
        result, code = ipu7.check(sysfs=self.drivers, run_probe=lambda: self.fail('Unexpected probe'))
        self.assertEqual((result['status'], code), ('not-applicable', 0))

    def test_healthy_host(self):
        result, code = ipu7.check(sysfs=self.drivers, run_probe=lambda: GOOD)
        self.assertEqual((result['status'], code), ('ok', 0))

    def test_failure_is_reported_without_repair(self):
        result, code = ipu7.check(sysfs=self.drivers, run_probe=lambda: BAD)
        self.assertEqual((result['status'], code), ('unresolved', 1))
        self.assertIn('undefined symbol:', result['details'])

    def test_probe_uses_host_defaults_without_capture(self):
        with patch.dict('os.environ', {'LD_LIBRARY_PATH': '/wrong', 'LD_PRELOAD': '/wrong', 'LIBCAMERA_IPA_MODULE_PATH': '/wrong'}):
            with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'Pixelformat: RGB')) as run:
                ipu7.probe()
        args, kwargs = run.call_args
        self.assertEqual(args[0], ['/usr/bin/cam', '-c', '1', '--info'])
        for key in ('LD_LIBRARY_PATH', 'LD_PRELOAD', 'LIBCAMERA_IPA_MODULE_PATH'):
            self.assertNotIn(key, kwargs['env'])
        self.assertEqual(kwargs['timeout'], 15)

    def test_zero_exit_with_ipa_failure_is_not_healthy(self):
        self.assertFalse(ipu7.usable(BAD))
        self.assertFalse(ipu7.usable((0, 'Available cameras:')))
        self.assertFalse(ipu7.usable((0, 'Pixelformat: RGB\nIPA init failed')))


if __name__ == '__main__':
    unittest.main()

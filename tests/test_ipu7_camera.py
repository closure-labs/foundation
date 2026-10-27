import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('ipu7', Path(__file__).resolve().parents[1] / 'modules/hosts/camera/ipu7/_check.py')
ipu7 = importlib.util.module_from_spec(SPEC)
_bytecode = sys.dont_write_bytecode
sys.dont_write_bytecode = True
try:
    SPEC.loader.exec_module(ipu7)
finally:
    sys.dont_write_bytecode = _bytecode
GOOD = (0, 'Available cameras:\nPixelformat: XRGB8888\n')
BAD = (0, ipu7.LEGACY + '/ipa_soft_simple.so: undefined symbol: foo\nIPA init failed\n')


class CameraTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.drivers = self.root / 'drivers'
        self.device = self.drivers / 'intel-ipu7/0000:00:05.0'
        self.device.mkdir(parents=True)
        self.config = self.root / 'configuration.yaml'
        self.config.write_text('module_paths: [' + ipu7.LEGACY + ']')
        self.modules = self.root / 'ipa'
        self.modules.mkdir()
        (self.modules / 'ipa_soft_simple.so').touch()
        self.user = self.root / 'user'

    def check(self, repair=False, probe=None):
        return ipu7.check(repair=repair, sysfs=self.drivers, config=self.config,
                          candidates=(self.modules,), user_config=self.user,
                          run_probe=probe or (lambda path=None: GOOD if path else BAD))

    def test_no_controller_never_probes_or_writes(self):
        self.device.rmdir()
        result, code = self.check(True, lambda _: self.fail('Unexpected probe'))
        self.assertEqual((result['status'], code), ('not-applicable', 0))
        self.assertFalse(self.user.exists())

    def test_healthy_host_not_overridden(self):
        result, code = self.check(True, lambda path=None: GOOD)
        self.assertEqual((result['status'], code), ('ok', 0))
        self.assertFalse(self.user.exists())

    def test_check_is_read_only_and_repair_idempotent(self):
        result, code = self.check()
        self.assertEqual((result['status'], code), ('repair-available', 1))
        self.assertFalse(self.user.exists())
        result, code = self.check(True)
        self.assertEqual((result['status'], code), ('configured', 0))
        p = Path(result['override'])
        self.assertIn(str(self.modules), p.read_text())
        mtime = p.stat().st_mtime_ns
        self.check(True)
        self.assertEqual(p.stat().st_mtime_ns, mtime)

    def test_unknown_failure_not_repaired(self):
        result, code = self.check(True, lambda path=None: (1, 'permission denied'))
        self.assertEqual((result['status'], code), ('unresolved', 1))
        self.assertFalse(self.user.exists())

    def test_bad_host_module_not_applied(self):
        result, code = self.check(True, lambda path=None: BAD)
        self.assertEqual((result['status'], code), ('unresolved', 1))
        self.assertFalse(self.user.exists())

    def test_missing_module_not_applied(self):
        (self.modules / 'ipa_soft_simple.so').unlink()
        self.assertEqual(self.check(True)[1], 1)
        self.assertFalse(self.user.exists())

    def test_custom_override_preserved(self):
        result, _ = self.check(True)
        p = Path(result['override'])
        p.write_text('user settings')
        self.assertEqual(self.check(True)[0]['status'], 'conflict')
        self.assertEqual(p.read_text(), 'user settings')

    def test_symlink_preserved(self):
        result, _ = self.check(True)
        p = Path(result['override'])
        p.unlink()
        p.symlink_to(self.config)
        self.assertEqual(self.check(True)[0]['status'], 'conflict')

    def test_probe_uses_host_abi_without_capture(self):
        with patch.dict('os.environ', {'LD_LIBRARY_PATH': '/wrong', 'LD_PRELOAD': '/wrong', 'LIBCAMERA_IPA_MODULE_PATH': '/wrong'}):
            with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'Pixelformat: RGB')) as run:
                ipu7.probe(self.modules)
        args, kwargs = run.call_args
        self.assertEqual(args[0], ['/usr/bin/cam', '-c', '1', '--info'])
        self.assertNotIn('LD_LIBRARY_PATH', kwargs['env'])
        self.assertNotIn('LD_PRELOAD', kwargs['env'])
        self.assertEqual(kwargs['env']['LIBCAMERA_IPA_MODULE_PATH'], str(self.modules))
        self.assertEqual(kwargs['timeout'], 15)

    def test_zero_exit_with_ipa_failure_is_not_healthy(self):
        self.assertFalse(ipu7.usable(BAD))
        self.assertFalse(ipu7.usable((0, 'Available cameras:')))
        self.assertFalse(ipu7.usable((0, 'Pixelformat: RGB\nIPA init failed')))


if __name__ == '__main__':
    unittest.main()

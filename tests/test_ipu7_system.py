import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location('system', Path(__file__).resolve().parents[1] / 'modules/hosts/camera/ipu7/_system.py')
system = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(system)


class SystemTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.target = root / 'policy.conf'
        self.record = root / 'policy.sha256'
        self.policy = root / 'source.conf'
        self.policy.write_bytes(system.MARKER + b'monitor.v4l2.rules = []\n')
        for name, value in [('TARGET', self.target), ('RECORD', self.record), ('POLICY', self.policy)]:
            p = patch.object(system, name, value)
            p.start()
            self.addCleanup(p.stop)
        for name in ('paths',):
            p = patch.object(system, name)
            p.start()
            self.addCleanup(p.stop)
        p = patch.object(system.os, 'fchown')
        p.start()
        self.addCleanup(p.stop)
        p = patch.object(system.subprocess, 'run')
        self.run = p.start()
        self.addCleanup(p.stop)

    def test_install_receipt_and_repeat_skip_sudo(self):
        system.apply('install')
        self.assertTrue(system.installed())
        with patch.object(system, 'detected', return_value=True), patch.object(system.sys, 'argv', ['installer', 'install']):
            self.run.reset_mock()
            system.main()
            self.run.assert_not_called()
        system.apply('uninstall')
        self.assertFalse(self.target.exists())
        self.assertFalse(self.record.exists())

    def test_custom_policy_preserved(self):
        self.target.write_bytes(b'custom')
        with self.assertRaisesRegex(RuntimeError, 'Preserving'):
            system.apply('install')
        self.assertEqual(self.target.read_bytes(), b'custom')

    def test_edited_managed_policy_preserved(self):
        system.apply('install')
        self.target.write_bytes(self.target.read_bytes() + b'user edit')
        for action in ('install', 'uninstall'):
            with self.assertRaisesRegex(RuntimeError, 'Preserving'):
                system.apply(action)

    def test_known_policy_can_update(self):
        system.apply('install')
        self.policy.write_bytes(system.MARKER + b'new policy\n')
        system.apply('install')
        self.assertTrue(system.installed())

    def test_failed_relabel_removes_new_policy_and_success_record(self):
        self.run.side_effect = OSError('failed relabel')
        with self.assertRaises(OSError):
            system.apply('install')
        self.assertFalse(self.target.exists())
        self.assertFalse(self.record.exists())

    def test_dry_run_never_escalates(self):
        with patch.object(system, 'detected', return_value=True), patch.object(system.sys, 'argv', ['installer', 'install', '--dry-run']):
            system.main()
        self.run.assert_not_called()
        self.assertFalse(self.target.exists())

    def test_unsupported_host_never_escalates(self):
        with patch.object(system, 'detected', return_value=False), patch.object(system.sys, 'argv', ['installer', 'install']):
            system.main()
        self.run.assert_not_called()

    def test_explanation_before_sudo(self):
        events = []
        self.run.side_effect = lambda *a, **k: events.append(a[0])
        with patch.object(system, 'detected', return_value=True), patch.object(system.os, 'geteuid', return_value=1000), patch.object(system.sys, 'argv', ['installer', 'install']), patch('builtins.print', side_effect=lambda *a, **k: events.append(str(a))):
            system.main()
        self.assertIn('Administrator access', events[0])
        self.assertEqual(events[1][:4], ['/usr/bin/sudo', '--', sys.executable, '-I'])


if __name__ == '__main__':
    unittest.main()

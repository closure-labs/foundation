"""Generation preparation is optional and stock bundle installation is bounded."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from test_home import home
SPEC = importlib.util.spec_from_file_location('bluefin_prepare', ROOT / 'modules/hosts/os/bluefin/_prepare.py')
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)


class Preparation(unittest.TestCase):
    def test_generation_entry_optional_and_executable_required(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(home, 'run') as run:
            generation = Path(temporary)
            home.prepare_generation(generation)
            run.assert_not_called()
            entry = generation / 'foundation-prepare'
            entry.write_text('#!/bin/sh\n')
            with self.assertRaises(ValueError): home.prepare_generation(generation)
            entry.chmod(0o755)
            home.prepare_generation(generation)
            run.assert_called_once_with([str(entry)])

    def test_ready_bundle_never_installs_and_missing_bundle_installs_once(self):
        for ready in (0, 1):
            with self.subTest(ready=ready), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                brew, bundle = root / 'brew', root / 'cli.Brewfile'
                brew.write_text('#!/bin/sh\n'); brew.chmod(0o755)
                bundle.write_text('brew "stock"\n')
                calls = []
                def run(command, **options):
                    calls.append(command[1:])
                    self.assertEqual(options['env']['HOMEBREW_NO_AUTO_UPDATE'], '1')
                    return subprocess.CompletedProcess(command, ready if len(calls) == 2 else 0, str(root))
                prepare.prepare(brew, bundle, run=run)
                installs = [row for row in calls if row[:2] == ['bundle', 'install']]
                self.assertEqual(len(installs), ready)
                if ready: self.assertIn('--no-upgrade', installs[0])
                self.assertTrue(all('optional' not in ' '.join(row) for row in calls))

    def test_install_failure_prevents_postcheck(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            brew, bundle = root / 'brew', root / 'cli.Brewfile'
            brew.touch(); brew.chmod(0o755); bundle.write_text('brew "stock"\n')
            calls = []
            def run(command, **kwargs):
                calls.append(command)
                if 'install' in command: raise subprocess.CalledProcessError(9, command)
                return subprocess.CompletedProcess(command, 1, str(root))
            with self.assertRaises(subprocess.CalledProcessError): prepare.prepare(brew, bundle, run=run)
            self.assertEqual(len(calls), 3)

    def test_stock_setup_wait_is_bounded_and_does_not_extract_or_elevate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bundle = root / 'cli.Brewfile'; bundle.write_text('')
            sleeps = []
            with self.assertRaises(ValueError): prepare.prepare(root / 'missing', bundle, sleep=sleeps.append)
            self.assertEqual(sleeps, [1] * 120)


if __name__ == '__main__': unittest.main()

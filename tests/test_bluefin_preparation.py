"""Generation preparation is optional and stock bundle installation is bounded."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
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
                prepare.prepare(brew, bundle, run=run, preinstall=root / 'missing-preinstall')
                installs = [row for row in calls if row[:2] == ['bundle', 'install']]
                checks = [row for row in calls if row[:2] == ['bundle', 'check']]
                self.assertEqual(len(installs), ready)
                if ready: self.assertIn('--no-upgrade', installs[0])
                self.assertEqual(len(checks), 2)
                self.assertTrue(all('--no-upgrade' in row for row in checks))
                self.assertTrue(all('optional' not in ' '.join(row) for row in calls))

    def test_outdated_installed_tools_satisfy_checks_without_installing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            brew, bundle = root / 'brew', root / 'cli.Brewfile'
            brew.touch(); brew.chmod(0o755); bundle.write_text('brew "outdated-but-installed"\n')
            calls = []
            def run(command, **kwargs):
                calls.append(command)
                # Model Homebrew's distinction: installed dependencies satisfy
                # --no-upgrade checks, while a normal check demands an upgrade.
                status = 0
                if command[1:3] == ['bundle', 'check']:
                    status = 0 if '--no-upgrade' in command else 1
                if command[1:3] == ['bundle', 'install']:
                    self.fail('Installed but outdated stock tools must not trigger installation')
                if kwargs.get('check') and status:
                    raise subprocess.CalledProcessError(status, command)
                return subprocess.CompletedProcess(command, status, str(root))
            with patch.dict(prepare.os.environ, {}, clear=True):
                prepare.prepare(brew, bundle, run=run, preinstall=root / 'missing-preinstall')
            self.assertEqual(sum(command[1:3] == ['bundle', 'check'] for command in calls), 2)

    def test_genuinely_missing_tools_install_once_and_must_pass_postcheck(self):
        for install_satisfies_bundle in (True, False):
            with self.subTest(install_satisfies_bundle=install_satisfies_bundle), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                brew, bundle = root / 'brew', root / 'cli.Brewfile'
                brew.touch(); brew.chmod(0o755); bundle.write_text('brew "missing"\n')
                calls, installed = [], False
                def run(command, **kwargs):
                    nonlocal installed
                    calls.append(command)
                    if command[1:3] == ['bundle', 'install']:
                        installed = install_satisfies_bundle
                    status = int(not installed) if command[1:3] == ['bundle', 'check'] else 0
                    if kwargs.get('check') and status:
                        raise subprocess.CalledProcessError(status, command)
                    return subprocess.CompletedProcess(command, status, str(root))
                if install_satisfies_bundle:
                    prepare.prepare(brew, bundle, run=run, preinstall=root / 'missing-preinstall')
                else:
                    with self.assertRaises(subprocess.CalledProcessError):
                        prepare.prepare(brew, bundle, run=run, preinstall=root / 'missing-preinstall')
                self.assertEqual(sum(command[1:3] == ['bundle', 'install'] for command in calls), 1)

    def test_existing_stock_setup_is_joined_as_a_synchronous_user_service(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            brew, bundle, preinstall = root / 'brew', root / 'cli.Brewfile', root / 'brew-preinstall'
            brew.touch(); brew.chmod(0o755); bundle.write_text('brew "stock"\n'); preinstall.touch()
            calls = []
            def run(command, **kwargs):
                calls.append(command)
                return subprocess.CompletedProcess(command, 0, str(root))
            prepare.prepare(brew, bundle, run=run, preinstall=preinstall)
            self.assertIn(['systemctl', '--user', 'start', 'brew-preinstall.service'], calls)
            self.assertFalse(any(str(preinstall) in command for command in calls))

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
            with self.assertRaises(subprocess.CalledProcessError):
                prepare.prepare(brew, bundle, run=run, preinstall=root / 'missing-preinstall')
            self.assertEqual(len(calls), 3)

    def test_stock_setup_wait_is_bounded_and_does_not_extract_or_elevate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bundle = root / 'cli.Brewfile'; bundle.write_text('')
            sleeps = []
            with self.assertRaises(ValueError): prepare.prepare(root / 'missing', bundle, sleep=sleeps.append)
            self.assertEqual(sleeps, [1] * 120)


if __name__ == '__main__': unittest.main()

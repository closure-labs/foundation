"""Only the Bluefin aspect delegates defaults to its inherited OS service."""
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

    def fixture(self, root):
        brew, preinstall = root / 'brew', root / 'brew-preinstall'
        for path in (brew, preinstall, root / 'fzf'):
            path.touch(); path.chmod(0o755)
        defaults = root / 'preinstall.d'; defaults.mkdir()
        (defaults / 'system-cli.Brewfile').write_text('brew "stock"\n')
        return brew, preinstall

    def state(self, **changes):
        fields = dict(LoadState='loaded', ActiveState='active', SubState='exited',
                      Result='success', ExecMainStatus='0', ConditionResult='yes')
        fields.update(changes)
        return ''.join(f'{key}={value}\n' for key, value in fields.items())

    def test_default_service_only_repeatable_without_optional_bundle_or_trust(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); brew, preinstall = self.fixture(root)
            calls = []
            def run(command, **options):
                calls.append(command)
                self.assertTrue(options['check'])
                self.assertLessEqual(options['timeout'], 600)
                return subprocess.CompletedProcess(command, 0, self.state())
            for _ in range(2):
                prepare.prepare(brew, run=run, preinstall=preinstall, fzf_paths=(root / 'fzf',), preinstall_dir=root / 'preinstall.d')
            self.assertEqual([row[2] for row in calls], ['start', 'show'] * 2)
            self.assertTrue(all(row[:2] == ['systemctl', '--user'] for row in calls))
            self.assertTrue(all('brew-preinstall.service' in row for row in calls))
            # No cli.Brewfile exists: default provisioning must not need it.
            self.assertFalse((root / 'cli.Brewfile').exists())

    def test_broken_upstream_provisioner_fails_before_service(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); brew, preinstall = self.fixture(root)
            for mode in ('not-executable',):
                preinstall.chmod(0o644)
                with patch.object(prepare.subprocess, 'run') as run:
                    with self.assertRaises(ValueError):
                        prepare.prepare(brew, run=run, preinstall=preinstall, fzf_paths=(root / 'fzf',), preinstall_dir=root / 'preinstall.d')
                    run.assert_not_called()

    def test_seed_wait_bounded_and_no_fallback_install(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); brew, preinstall = self.fixture(root); brew.unlink()
            sleeps = []
            with self.assertRaises(ValueError):
                prepare.prepare(brew, sleep=sleeps.append, preinstall=preinstall, fzf_paths=(root / 'fzf',), preinstall_dir=root / 'preinstall.d')
            self.assertEqual(sleeps, [1] * 120)

    def test_service_failure_or_timeout_prevents_postcheck(self):
        for error in (subprocess.CalledProcessError(1, ['systemctl']),
                      subprocess.TimeoutExpired(['systemctl'], 600)):
            with self.subTest(error=error), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); brew, preinstall = self.fixture(root)
                with patch.object(prepare.subprocess, 'run', side_effect=error) as run:
                    with self.assertRaises(type(error)):
                        prepare.prepare(brew, run=run, preinstall=preinstall, fzf_paths=(root / 'fzf',), preinstall_dir=root / 'preinstall.d')
                    self.assertEqual(run.call_count, 1)

    def test_skipped_failed_incomplete_or_malformed_service_is_not_ready(self):
        states = [self.state(**change) for change in (
            {'LoadState':'not-found'}, {'ActiveState':'inactive'}, {'SubState':'running'},
            {'Result':'exit-code'}, {'ExecMainStatus':'1'}, {'ConditionResult':'no'})]
        states += ['', self.state() + 'Result=success\n', 'invalid', self.state() + 'Unknown=yes\n']
        for state in states:
            with self.subTest(state=state), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); brew, preinstall = self.fixture(root)
                def run(command, **options):
                    return subprocess.CompletedProcess(command, 0, state)
                with self.assertRaises(ValueError):
                    prepare.prepare(brew, run=run, preinstall=preinstall, fzf_paths=(root / 'fzf',), preinstall_dir=root / 'preinstall.d')

    def test_preinstall_exit_zero_skip_conditions_are_rejected_before_start(self):
        for case in ('missing-defaults', 'empty-defaults', 'greeter'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); brew, preinstall = self.fixture(root)
                defaults = root / 'preinstall.d'
                if case != 'greeter':
                    (defaults / 'system-cli.Brewfile').unlink()
                    if case == 'missing-defaults': defaults.rmdir()
                env = {'USER': 'gdm-test'} if case == 'greeter' else {'USER': 'alice', 'HOME': str(root)}
                with patch.dict(prepare.os.environ, env), patch.object(prepare.subprocess, 'run') as run:
                    with self.assertRaises(ValueError):
                        prepare.prepare(brew, run=run, preinstall=preinstall,
                                        preinstall_dir=defaults, fzf_paths=(root / 'fzf',))
                    run.assert_not_called()

    def test_older_image_checks_seed_without_starting_any_service(self):
        for condition in ('yes', 'no'):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); brew, preinstall = self.fixture(root); preinstall.unlink()
                calls = []
                def run(command, **options):
                    calls.append(command)
                    return subprocess.CompletedProcess(command, 0, self.state(
                        ActiveState='inactive', SubState='dead', ConditionResult=condition))
                prepare.prepare(brew, run=run, preinstall=preinstall, fzf_paths=(root / 'fzf',), preinstall_dir=root / 'preinstall.d')
                self.assertEqual(calls[0][:3], ['systemctl', 'show', 'brew-setup.service'])
                self.assertEqual(len(calls), 1)

    def test_older_seed_failure_or_stalled_start_fails_closed(self):
        for active, result in (('failed', 'exit-code'), ('activating', 'success')):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); brew, preinstall = self.fixture(root); preinstall.unlink()
                sleeps = []
                def run(command, **options):
                    return subprocess.CompletedProcess(command, 0, self.state(ActiveState=active, Result=result))
                with self.assertRaises(ValueError):
                    prepare.prepare(brew, run=run, sleep=sleeps.append, preinstall=preinstall,
                                    fzf_paths=(root / 'fzf',), preinstall_dir=root / 'preinstall.d')
                self.assertEqual(len(sleeps), 120 if active == 'activating' else 0)

    def test_missing_or_nonexecutable_stock_fzf_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); brew, preinstall = self.fixture(root)
            def run(command, **options):
                return subprocess.CompletedProcess(command, 0, self.state())
            for mode in ('missing', 'not-executable'):
                fzf = root / 'fzf'
                if mode == 'missing': fzf.unlink()
                else: fzf.touch(); fzf.chmod(0o644)
                with self.assertRaisesRegex(ValueError, 'fzf'):
                    prepare.prepare(brew, run=run, preinstall=preinstall, fzf_paths=(root / 'fzf',), preinstall_dir=root / 'preinstall.d')


if __name__ == '__main__': unittest.main()

"""Realization recovery never repeats initialization or activation."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('home_transport', Path(__file__).resolve().parents[1] / 'scripts/home.py')
home = importlib.util.module_from_spec(spec)
spec.loader.exec_module(home)
URL = 'https://cache.nixos.org/nar/fixture.nar.zst'
INTERRUPTED = f"warning: unable to download '{URL}': HTTP error 200 (curl error: Failure when receiving data from the peer); retrying from offset 1234 in 20 ms (attempt 1/5)\n"
RANGE = f"error: unable to download '{URL}': HTTP error 416\n"


class Recovery(unittest.TestCase):
    def setUp(self):
        self.now, self.calls, self.delays = 0, [], []
        self.results = [(1, INTERRUPTED + RANGE), (0, '')]

    def clock(self): return self.now

    def sleep(self, seconds):
        self.delays.append(seconds)
        self.now += seconds

    def execute(self, command, timeout):
        self.calls.append(timeout)
        self.now += 1
        status, error = self.results.pop(0)
        return subprocess.CompletedProcess(command, status, '/nix/store/activation\n', error)

    def realize(self):
        return home.capture_build(['fixture-nix', 'build'], clock=self.clock, sleep=self.sleep, execute=self.execute)

    def test_verified_interruption_restarts_only_realization(self):
        self.assertEqual(self.realize(), '/nix/store/activation')
        self.assertEqual(self.calls, [900, 897])
        self.assertEqual(self.delays, [2])

    def test_three_total_attempts_and_two_four_backoff(self):
        self.results = [(1, INTERRUPTED + RANGE)] * 3
        with self.assertRaises(subprocess.CalledProcessError): self.realize()
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(self.delays, [2, 4])

    def test_nested_attempts_and_backoff_share_deadline(self):
        def slow(command, timeout):
            self.now += 899
            return subprocess.CompletedProcess(command, 1, '', INTERRUPTED + RANGE)
        with self.assertRaises(subprocess.TimeoutExpired):
            home.capture_build(['fixture'], clock=self.clock, sleep=self.sleep, execute=slow)
        self.assertEqual(self.delays, [])

    def test_auth_integrity_evaluation_build_and_unverified_range_are_terminal(self):
        for error in (RANGE, INTERRUPTED.replace(URL, URL + '-other') + RANGE,
                      'HTTP error 401', 'HTTP error 403', 'HTTP error 404',
                      'hash mismatch in fixed-output derivation', 'invalid signature verification failed',
                      'syntax error', 'undefined variable', "builder for '/nix/store/test.drv' failed with exit code 1"):
            self.setUp()
            self.results = [(1, INTERRUPTED + RANGE + error)] if error != RANGE else [(1, RANGE)]
            if '-other' in error: self.results = [(1, error)]
            with self.subTest(error=error), self.assertRaises(subprocess.CalledProcessError): self.realize()
            self.assertEqual(len(self.calls), 1)
            self.assertEqual(self.delays, [])

    def test_transient_http_retry_and_signal_failures(self):
        self.results = [(1, 'error: unable to download fixture: HTTP error 503'), (0, '')]
        self.assertEqual(self.realize(), '/nix/store/activation')
        self.setUp()
        self.results = [(-15, INTERRUPTED + RANGE)]
        with self.assertRaises(subprocess.CalledProcessError): self.realize()
        self.assertEqual(self.delays, [])

    def test_wrapper_and_usage_exits_are_terminal_even_with_transient_diagnostics(self):
        for status in (-9, -15, 2, 126, 127, 128, 130, 137, 143, 255):
            self.setUp()
            self.results = [(status, INTERRUPTED + RANGE)]
            with self.subTest(status=status), self.assertRaises(subprocess.CalledProcessError): self.realize()
            self.assertEqual(len(self.calls), 1)
            self.assertEqual(self.delays, [])

    def test_kill_diagnostics_are_terminal_even_if_wrapper_uses_exit_one(self):
        for diagnostic in ('Killed', 'SIGKILL', 'terminated by signal 9', 'Out of memory', 'oom-killed'):
            self.setUp()
            self.results = [(1, INTERRUPTED + RANGE + diagnostic)]
            with self.subTest(diagnostic=diagnostic), self.assertRaises(subprocess.CalledProcessError): self.realize()
            self.assertEqual(len(self.calls), 1)
            self.assertEqual(self.delays, [])

    def test_resume_proof_must_precede_the_same_url_failure(self):
        self.assertFalse(home.download_retryable(RANGE + INTERRUPTED))
        self.assertFalse(home.download_retryable(INTERRUPTED + RANGE + RANGE.replace(URL, URL + '-unverified')))

    def test_transient_diagnostics_never_hide_other_root_errors(self):
        for error in ("error: expected a set but found a string", "       error: expected a set but found a string", "error: disk full",
                      "error: unable to download 'https://other': SSL certificate problem",
                      "error: Cannot build '/nix/store/other.drv'.\n       Reason: builder failed with exit code 1."):
            with self.subTest(error=error):
                self.assertFalse(home.download_retryable(INTERRUPTED + RANGE + error))
        cascade = ("error: path '/nix/store/package' is required, but there is no substituter that can build it\n"
                   "error: some substitutes for the outputs of derivation '/nix/store/package.drv' failed (usually happens due to networking issues); try '--fallback' to build derivation from source\n"
                   "error: Cannot build '/nix/store/home.drv'.\n       Reason: 1 dependency failed.\n       Output paths:\n         /nix/store/home\n")
        self.assertTrue(home.download_retryable(INTERRUPTED + RANGE + cascade))

    def test_actual_subprocess_streams_errors_and_deadline_kills_its_group(self):
        result = home.build_attempt([sys.executable, '-c', "import sys; print('path'); print('diagnostic', file=sys.stderr); sys.exit(1)"], 5)
        self.assertEqual(result.stdout, 'path\n')
        self.assertIn('diagnostic', result.stderr)
        with self.assertRaises(subprocess.TimeoutExpired):
            home.build_attempt([sys.executable, '-c', 'import time; time.sleep(30)'], 0.05)

    def test_partial_user_configuration_never_removed_or_reinitialized(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'home-manager'; root.mkdir()
            partial = root / 'customize.nix'; partial.write_text('user-owned partial initialization\n')
            with patch.object(home, 'capture_build') as realize, self.assertRaisesRegex(ValueError, 'already exists'):
                home.initialize(root, Path(directory) / 'profile.json')
            realize.assert_not_called()
            self.results = [(1, INTERRUPTED + RANGE)] * 3
            with self.assertRaises(subprocess.CalledProcessError): self.realize()
            self.assertEqual(partial.read_text(), 'user-owned partial initialization\n')
            self.assertEqual(sorted(p.name for p in root.iterdir()), ['customize.nix'])


if __name__ == '__main__': unittest.main()

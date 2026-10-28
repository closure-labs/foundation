"""Focused shared-owner changes must execute, and enforce, Nix contracts."""
import contextlib
import io
import json
import os
import subprocess
import unittest
from unittest.mock import patch

import nix_checks


class NixChecksTests(unittest.TestCase):
    def run_focused(self, path, execute):
        plan = nix_checks.make_plan([path], baseline="a" * 40)
        with patch.dict(os.environ, {"CI_PLAN": json.dumps(plan)}), \
                patch.object(nix_checks.sys, "argv", ["nix_checks.py", "--ci", "--no-build"]), \
                patch.object(nix_checks.os, "chdir"), \
                patch.object(nix_checks, "subprocess") as process, \
                contextlib.redirect_stdout(io.StringIO()):
            process.run.side_effect = execute
            nix_checks.main()

    def test_focused_policy_and_root_changes_execute_both_contracts(self):
        for path in ("modules/providers/nixpkgs/_package-sets.nix",
                     "modules/home/construction/_config-root.nix",
                     "modules/flake/exports/_api.nix"):
            commands = []
            with self.subTest(path=path):
                self.run_focused(path, lambda command, **kwargs: commands.append(command))
                scripts = [command[1] for command in commands if command[0] == nix_checks.sys.executable]
                self.assertIn("tests/nix_package_policy_validation.py", scripts)
                self.assertIn("tests/nix_config_root_validation.py", scripts)

    def test_failed_contract_stops_focused_validation(self):
        commands = []

        def execute(command, **kwargs):
            commands.append(command)
            self.assertTrue(kwargs["check"])
            if "tests/nix_package_policy_validation.py" in command:
                raise subprocess.CalledProcessError(1, command)

        with self.assertRaises(subprocess.CalledProcessError):
            self.run_focused("modules/providers/nixpkgs/_package-sets.nix", execute)
        self.assertEqual(commands[-1][1], "tests/nix_package_policy_validation.py")
        self.assertFalse(any("tests/nix_schema3_validation.py" in command for command in commands))


if __name__ == "__main__":
    unittest.main()

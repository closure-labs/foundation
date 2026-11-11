"""Opt-in timings preserve command order, failure identity and configuration."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("timed_home", ROOT / "scripts/home.py")
home = importlib.util.module_from_spec(spec)
spec.loader.exec_module(home)


class Timings(unittest.TestCase):
    def records(self, output):
        return [json.loads(line.removeprefix("FOUNDATION_TIMING "))
                for line in output.getvalue().splitlines() if line.startswith("FOUNDATION_TIMING ")]

    def test_disabled_diagnostics_add_no_output_or_clock_reads(self):
        for value in ("", "0", "false", "true"):
            with self.subTest(value=value), patch.dict(os.environ, FOUNDATION_TIMINGS=value), \
                    patch.object(home.time, "monotonic") as clock, contextlib.redirect_stderr(io.StringIO()) as output:
                with home.timing("activation"):
                    pass
                self.assertEqual(output.getvalue(), "")
                clock.assert_not_called()

    def test_nested_success_records_have_bounded_fields_and_no_command_data(self):
        with patch.dict(os.environ, FOUNDATION_TIMINGS="1"), \
                patch.object(home.time, "monotonic", side_effect=[1., 2., 4., 6.]), \
                contextlib.redirect_stderr(io.StringIO()) as output:
            with home.timing("initialization"):
                with home.timing("activation"):
                    pass
        records = self.records(output)
        self.assertEqual([(r["stage"], r["seconds"]) for r in records], [("activation", 2.), ("initialization", 5.)])
        for row in records:
            self.assertEqual(set(row), {"schema", "kind", "authorizesPublication", "stage", "startedAt", "seconds", "outcome", "status"})
            self.assertEqual(row["kind"], "foundation-stage-timing")
            self.assertEqual((row["outcome"], row["status"]), ("success", 0))
            self.assertFalse(row["authorizesPublication"])
            self.assertLess(len(json.dumps(row)), 512)

    def test_failures_keep_original_exception_and_partial_stage(self):
        for failure in (ValueError("private path"), subprocess.CalledProcessError(7, ["private-command"]),
                        subprocess.TimeoutExpired(["private-command"], 5), KeyboardInterrupt()):
            with self.subTest(failure=type(failure).__name__), patch.dict(os.environ, FOUNDATION_TIMINGS="1"), \
                    contextlib.redirect_stderr(io.StringIO()) as output:
                with self.assertRaises(type(failure)) as raised:
                    with home.timing("home-manager-realisation"):
                        raise failure
                self.assertIs(raised.exception, failure)
                row, = self.records(output)
                self.assertEqual(row["outcome"], "error")
                self.assertEqual(row["status"], 7 if isinstance(failure, subprocess.CalledProcessError) else None)
                self.assertNotIn("private", output.getvalue())

    def test_failed_diagnostic_output_does_not_change_success_or_failure(self):
        class Broken:
            def write(self, value):
                raise OSError("full diagnostic sink")
        with patch.dict(os.environ, FOUNDATION_TIMINGS="1"), contextlib.redirect_stderr(Broken()):
            with home.timing("activation"):
                pass
            failure = ValueError("actual failure")
            with self.assertRaises(ValueError) as raised:
                with home.timing("activation"):
                    raise failure
            self.assertIs(raised.exception, failure)

    def test_realisation_retries_keep_single_outer_stage_and_exact_command(self):
        command = ["systemd-run", "--scope", "nix", "build", "--max-jobs", "1", "--cores", "1", "immutable"]
        calls = []
        def execute(actual, timeout):
            calls.append((actual, timeout))
            return subprocess.CompletedProcess(actual, 1 if len(calls) == 1 else 0,
                                               "/nix/store/activation\n", "error: unable to download fixture: HTTP error 503")
        with patch.dict(os.environ, FOUNDATION_TIMINGS="1"), contextlib.redirect_stderr(io.StringIO()) as output:
            result = home.capture_build(command, execute=execute, sleep=lambda _: None)
        self.assertEqual(result, "/nix/store/activation")
        self.assertEqual([c[0] for c in calls], [command, command])
        self.assertEqual([r["stage"] for r in self.records(output)], ["home-manager-realisation"])

    def test_enabled_build_keeps_resource_limits_and_one_realization_command(self):
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            profile = {"identity": {"username": "fixture"}}
            (stage / "profile.json").write_text(json.dumps(profile))
            activation = stage / "generation"
            activation.mkdir()
            (activation / "activate").touch()
            commands = []
            def execute(command, timeout):
                commands.append(command)
                return subprocess.CompletedProcess(command, 0, str(activation), "")
            for enabled in ("", "1"):
                with patch.dict(os.environ, FOUNDATION_TIMINGS=enabled, FOUNDATION_BUILD_MEMORY_MAX="5G"), \
                        patch.object(home, "validate_staged_profile", return_value=profile), \
                        patch.object(home, "build_attempt", side_effect=execute), \
                        contextlib.redirect_stderr(io.StringIO()) as output:
                    self.assertEqual(home.build(stage), activation)
                self.assertEqual(len(self.records(output)), 1 if enabled else 0)
            self.assertEqual(len(commands), 2)
            self.assertEqual(commands[0], [item for item in commands[1] if item not in ("--log-format", "internal-json") and not item.startswith("--unit=")])
            self.assertEqual([item for item in commands[1] if not item.startswith("--unit=")][:12], ["systemd-run", "--user", "--scope", "--quiet",
                "-p", "MemoryMax=5G", "-p", "MemorySwapMax=512M", "-p", "CPUQuota=100%", "nix", "build"])
            self.assertEqual([item for item in commands[1] if not item.startswith("--unit=")][12:16], ["--max-jobs", "1", "--cores", "1"])

    def test_failed_initialization_preserves_existing_configuration_without_build(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "home-manager"
            root.mkdir()
            custom = root / "customize.nix"
            custom.write_text("user-owned content\n")
            with patch.dict(os.environ, FOUNDATION_TIMINGS="1"), patch.object(home, "build") as build, \
                    patch.object(home, "prepare_generation") as brew, patch.object(home, "commit_stage") as activate, \
                    contextlib.redirect_stderr(io.StringIO()) as output, self.assertRaises(ValueError):
                home.initialize(root, root / "profile.json")
            self.assertEqual(custom.read_text(), "user-owned content\n")
            for action in (build, brew, activate):
                action.assert_not_called()
            row, = self.records(output)
            self.assertEqual((row["stage"], row["outcome"]), ("initialization", "error"))

    def test_initialization_build_brew_and_activation_run_once_in_order(self):
        for enabled in ("", "1"):
            for check in (False, True):
                with self.subTest(enabled=enabled, check=check), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory) / "home-manager"
                    calls = []
                    def template(source, info, stage):
                        stage.mkdir()
                    def build(stage):
                        calls.append("build")
                        return Path("/nix/store/fixture")
                    with patch.dict(os.environ, FOUNDATION_TIMINGS=enabled), \
                            patch.object(home, "capture", return_value=json.dumps({"schema": 3, "identity": {}})), \
                            patch.object(home, "profile_capabilities", return_value={"initializeSchemas": [3]}), \
                            patch.object(home, "source_root", return_value=ROOT), \
                            patch.object(home, "make_template", side_effect=template), \
                            patch.object(home, "build", side_effect=build), \
                            patch.object(home, "prepare_generation", side_effect=lambda _: calls.append("brew")), \
                            patch.object(home, "commit_stage", side_effect=lambda *args: calls.append("activate")), \
                            contextlib.redirect_stderr(io.StringIO()) as output:
                        home.initialize(root, root / "profile.json", check=check)
                    self.assertEqual(calls, ["build"] if check else ["build", "brew", "activate"])
                    self.assertEqual(len(self.records(output)), 1 if enabled else 0)


if __name__ == "__main__":
    unittest.main()

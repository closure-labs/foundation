"""Stable release automation preserves the owner/generated-artifact transaction."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("home_release", ROOT / "scripts/advance-home-release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class HomeReleaseTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / ".tack").mkdir()
        (self.root / release.PINS).write_text(
            """
[inputs.core.nixpkgs]
url = "https://flakehub.com/f/DeterminateSystems/nixpkgs-26.05-chilled/0.1"

[inputs.core.home-manager]
url = "https://flakehub.com/f/nix-community/home-manager/0.2605"

[inputs.office.office-stable]
url = "https://flakehub.com/f/DeterminateSystems/nixpkgs-26.05-chilled/0.1"

[inputs.password-managers.passwords-stable]
url = "https://flakehub.com/f/DeterminateSystems/nixpkgs-26.05-chilled/0.1"
# personal comment
"""
        )
        (self.root / release.LOCK).write_text("old lock")
        self.before = self.snapshot()

    def snapshot(self):
        return {relative: (self.root / relative).read_bytes() for relative in (release.PINS, release.LOCK)}

    def test_next_release_handles_both_boundaries(self):
        self.assertEqual(release.next_series("26.05"), "26.11")
        self.assertEqual(release.next_series("26.11"), "27.05")

    def test_tack_declarations_are_authoritative(self):
        (self.root / "flake.nix").write_text("generated output is deliberately stale")
        self.assertEqual(release.stable_pair(self.root), "26.05")

    def test_malformed_duplicate_and_mismatched_owners_fail_before_network(self):
        path = self.root / release.PINS
        original = path.read_text()
        for text in ("", original * 2, original.replace("0.2605", "0.2611")):
            with self.subTest(text=text), patch.object(release, "available") as availability:
                path.write_text(text)
                with self.assertRaises((ValueError, KeyError)):
                    release.advance(self.root)
                availability.assert_not_called()

    def test_unavailable_pair_does_not_mutate(self):
        with patch.object(release, "available", return_value=False), patch.object(release.subprocess, "run") as run:
            self.assertFalse(release.advance(self.root))
        run.assert_not_called()
        self.assertEqual(self.snapshot(), self.before)

    def test_advances_the_core_pair_and_stable_app_pins(self):
        def run(command, **kwargs):
            self.assertEqual(release.stable_pair(self.root), "26.11")
            self.assertEqual(command[-4:], list(release.STABLE_PINS))
            self.assertEqual(kwargs, {"cwd": self.root, "check": True})
            (self.root / release.LOCK).write_text("new lock")

        with patch.object(release, "available", return_value=True), patch.object(release.subprocess, "run", side_effect=run):
            self.assertTrue(release.advance(self.root))
        self.assertIn("# personal comment", (self.root / release.PINS).read_text())
        self.assertEqual((self.root / release.LOCK).read_text(), "new lock")

    def test_failed_tack_update_restores_both_files(self):
        def run(command, **kwargs):
            (self.root / release.LOCK).write_text("partial output")
            raise subprocess.CalledProcessError(1, command)

        with patch.object(release, "available", return_value=True), patch.object(release.subprocess, "run", side_effect=run):
            with self.assertRaises(subprocess.CalledProcessError):
                release.advance(self.root)
        self.assertEqual(self.snapshot(), self.before)

    def test_branch_not_ready_is_not_a_network_failure(self):
        with patch.object(release.subprocess, "run", return_value=subprocess.CompletedProcess([], 2)), patch.object(release.urllib.request, "urlopen") as fetch:
            self.assertFalse(release.available("26.11"))
            fetch.assert_not_called()
        with patch.object(release.subprocess, "run", return_value=subprocess.CompletedProcess([], 128)):
            with self.assertRaises(subprocess.CalledProcessError):
                release.available("26.11")

    def test_checks_both_branches_and_mirrors(self):
        with patch.object(release.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run, patch.object(release.urllib.request, "urlopen", return_value=MagicMock()) as fetch:
            self.assertTrue(release.available("26.11"))
        self.assertEqual([c.args[0][-1] for c in run.call_args_list], ["refs/heads/nixos-26.11", "refs/heads/release-26.11"])
        self.assertEqual([c.args[0] for c in fetch.call_args_list], [
            "https://flakehub.com/f/DeterminateSystems/nixpkgs-26.11-chilled/0.1",
            "https://flakehub.com/f/nix-community/home-manager/0.2611",
        ])

    def test_only_mirror_404_means_not_yet_available(self):
        for code in (404, 500):
            error = urllib.error.HTTPError("https://flakehub.com", code, "fixture", {}, None)
            with self.subTest(code=code), patch.object(release.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)), patch.object(release.urllib.request, "urlopen", side_effect=error):
                if code == 404:
                    self.assertFalse(release.available("26.11"))
                else:
                    with self.assertRaises(urllib.error.HTTPError):
                        release.available("26.11")

    def test_workflow_submits_every_transaction_path(self):
        workflow = (ROOT / ".github/workflows/home-release.yml").read_text()
        paths = workflow.split("          add-paths: |\n", 1)[1].split("          branch:", 1)[0]
        self.assertEqual(set(paths.split()), {release.PINS, release.LOCK})


if __name__ == "__main__":
    unittest.main()

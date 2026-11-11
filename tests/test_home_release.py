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
        for relative in release.TRANSACTION_PATHS:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("original fixture: " + relative + "\n")
        (self.root / release.NIXPKGS_OWNER).write_text(
            '{ ... }: { flake-file.inputs.nixpkgs.url = '
            '"https://flakehub.com/f/DeterminateSystems/nixpkgs-26.05-chilled/0.1"; }\n'
        )
        (self.root / release.HOME_MANAGER_OWNER).write_text(
            '{ ... }: { flake-file.inputs.home-manager.url = '
            '"https://flakehub.com/f/nix-community/home-manager/0.2605"; }\n'
        )
        # An unrelated local edit must survive both successful and failed updates.
        with (self.root / release.NIXPKGS_OWNER).open("a") as owner:
            owner.write("\n# personal comment\n")
        self.before = self.snapshot()

    def snapshot(self):
        return {relative: (self.root / relative).read_bytes() for relative in release.TRANSACTION_PATHS}

    def test_advanced_checkout_series_does_not_change_fixture_baseline(self):
        # The workflow runs this suite AFTER advancing the real checkout. Reading
        # live owner files in setUp would make the hardcoded fixture expectations
        # fail exactly when a new stable release becomes available.
        original_read = Path.read_bytes

        def read(path):
            if path in (ROOT / release.NIXPKGS_OWNER, ROOT / release.HOME_MANAGER_OWNER):
                raise AssertionError("Tests must not read the checkout's current release owners")
            return original_read(path)

        fixture = HomeReleaseTests("test_owner_declarations_are_authoritative")
        with patch.object(Path, "read_bytes", read):
            fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.assertEqual(release.stable_pair(fixture.root), "26.05")

    def test_next_release_handles_both_boundaries(self):
        self.assertEqual(release.next_series("26.05"), "26.11")
        self.assertEqual(release.next_series("26.11"), "27.05")

    def test_owner_declarations_are_authoritative(self):
        (self.root / "flake.nix").write_text("generated output is deliberately stale")
        self.assertEqual(release.stable_pair(self.root), "26.05")

    def test_malformed_duplicate_and_mismatched_owners_fail_before_network(self):
        path = self.root / release.HOME_MANAGER_OWNER
        original = path.read_text()
        for text in ("", original * 2, original.replace("0.2605", "0.2611")):
            with self.subTest(text=text), patch.object(release, "available") as availability:
                path.write_text(text)
                with self.assertRaises(ValueError):
                    release.advance(self.root)
                availability.assert_not_called()

    def test_unavailable_pair_does_not_mutate(self):
        with patch.object(release, "available", return_value=False), patch.object(release.subprocess, "run") as run:
            self.assertFalse(release.advance(self.root))
        run.assert_not_called()
        self.assertEqual(self.snapshot(), self.before)

    def test_updates_owners_then_generates_locks_and_graph(self):
        commands = []

        def run(command, **kwargs):
            commands.append(command)
            self.assertEqual(kwargs, {"cwd": self.root, "check": True})
            self.assertEqual(release.stable_pair(self.root), "26.11")
            if command[-1] == "path:.#write-flake":
                self.assertEqual((self.root / "flake.nix").read_bytes(), self.before["flake.nix"])
                (self.root / "flake.nix").write_text("generated from updated owners")
            elif command[1:3] == ["flake", "update"]:
                self.assertEqual((self.root / "flake.nix").read_text(), "generated from updated owners")
                (self.root / "flake.lock").write_text("updated pair lock")
            elif command[-1] == "path:.#write-ci-graph":
                self.assertEqual((self.root / "flake.lock").read_text(), "updated pair lock")
                (self.root / "modules/ci/_graph.json").write_text("updated graph")
                (self.root / "docs/ARCHITECTURE.md").write_text("updated diagram")

        with patch.object(release, "available", return_value=True), patch.object(release.subprocess, "run", side_effect=run):
            self.assertTrue(release.advance(self.root))
        self.assertEqual(commands, [
            ["nix", "run", "--no-update-lock-file", "path:.#write-flake"],
            ["nix", "flake", "update", "nixpkgs", "home-manager"],
            ["nix", "run", "--no-update-lock-file", "path:.#write-ci-graph"],
        ])
        self.assertIn("# personal comment", (self.root / release.NIXPKGS_OWNER).read_text())

    def test_every_failed_stage_restores_all_original_bytes(self):
        for failed_stage in range(3):
            count = 0

            def run(command, **kwargs):
                nonlocal count
                # Simulate partial output, including files changed by earlier stages.
                for relative in release.TRANSACTION_PATHS[2:]:
                    (self.root / relative).write_text("partial output")
                if count == failed_stage:
                    raise subprocess.CalledProcessError(1, command)
                count += 1

            with self.subTest(stage=failed_stage), patch.object(release, "available", return_value=True), patch.object(release.subprocess, "run", side_effect=run):
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
        self.assertEqual(set(paths.split()), set(release.TRANSACTION_PATHS))


if __name__ == "__main__":
    unittest.main()

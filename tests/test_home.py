"""Exercise consumer locks, migrations, transactional updates and notifications."""
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("foundation_home", ROOT / "scripts/home.py")
home = importlib.util.module_from_spec(spec)
spec.loader.exec_module(home)
INFO = {"schema": 1, "compatibility": 1, "version": "0.2.0", "rev": "a" * 40,
        "narHash": "sha256-" + "A" * 43 + "=", "lastModified": 1}
LOCK = {"version": 7, "root": "root", "nodes": {
    "root": {"inputs": {"nixpkgs": "pkgs", "gen": "gen"}},
    "pkgs": {"locked": {"type": "github", "rev": "old-pkgs"}},
    "gen": {"inputs": {"nixpkgs": ["nixpkgs"]}, "locked": {"type": "github", "rev": "old-gen"}},
}}


class ConsumerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "home-manager"
        home.make_template(ROOT, INFO, self.root, LOCK)
        self.activation = self.base / "generation"
        self.activation.mkdir()
        (self.activation / "activate").write_text("#!/bin/sh\nexit 0\n")
        (self.activation / "activate").chmod(0o755)

    def test_lock_re_roots_follows_and_keeps_exact_pins(self):
        lock = home.consumer_lock(LOCK, INFO)
        self.assertEqual(lock["nodes"]["foundation-gen"]["inputs"]["nixpkgs"], ["foundation", "nixpkgs"])
        self.assertEqual(lock["nodes"]["foundation-pkgs"]["locked"], LOCK["nodes"]["pkgs"]["locked"])
        self.assertEqual(lock["nodes"]["root"]["inputs"], {"foundation": "foundation"})
        self.assertNotIn("espanso", json.dumps(lock))

    def test_rejects_unpinned_or_unsupported_sources(self):
        for changes in ({"rev": None}, {"compatibility": 2}, {"narHash": "bad"}):
            with self.assertRaises(ValueError):
                home.validate_metadata({**INFO, **changes})

    def test_update_rejects_dependency_drift_and_personal_pin_changes(self):
        before = home.consumer_lock(LOCK, INFO)
        after = copy.deepcopy(before)
        candidate = {**INFO, "version": "0.3.0", "rev": "b" * 40}
        after = home.consumer_lock(LOCK, candidate)
        home.verify_update_lock(before, after, LOCK, candidate)
        after["nodes"]["foundation-pkgs"]["locked"]["rev"] = "unexpected"
        with self.assertRaisesRegex(ValueError, "published release lock"):
            home.verify_update_lock(before, after, LOCK, candidate)
        after = home.consumer_lock(LOCK, candidate)
        for lock in (before, after):
            lock["nodes"]["root"]["inputs"]["personal"] = "personal"
            lock["nodes"]["personal"] = {"locked": {"rev": "private-pin"}}
        after["nodes"]["personal"]["locked"]["rev"] = "changed"
        with self.assertRaisesRegex(ValueError, "personal input"):
            home.verify_update_lock(before, after, LOCK, candidate)

    def test_personal_input_nix_strings_are_literal(self):
        text = home.consumer_flake(INFO, {"personal": {"url": "file:///some/${literal}", "flake": False}})
        self.assertIn(r"\${literal}", text)
        self.assertIn('"flake" = false;', text)
        self.assertEqual(len(home.REFERENCE.findall(text)), 1)

    def test_templates_track_channel_with_an_immutable_lock(self):
        text = (self.root / "flake.nix").read_text()
        lock = home.read_json(self.root / "flake.lock")
        self.assertIn("/latest-release", text)
        self.assertEqual(lock["nodes"]["foundation"]["original"]["ref"], "latest-release")
        self.assertEqual(lock["nodes"]["foundation"]["locked"]["rev"], INFO["rev"])
        self.assertEqual(len(home.REFERENCE.findall((ROOT / "templates/default/flake.nix").read_text())), 1)

    def test_nh_lock_update_overrides_stale_cached_provenance_without_writes(self):
        candidate = {**INFO, "version": "0.3.0", "rev": "b" * 40}
        home.write_json(self.root / "flake.lock", home.consumer_lock(LOCK, candidate))
        before = home.tree_digest(self.root)
        with patch.object(home, "capture", return_value=json.dumps({"schema": 1, "compatibility": 1, "version": "0.3.0"})) as capture:
            self.assertEqual(home.installed_info(self.root), candidate)
        self.assertIn(candidate["rev"], capture.call_args.args[0][-1])
        self.assertEqual(home.tree_digest(self.root), before)

    def test_lock_repository_cannot_be_hidden_by_cached_provenance(self):
        lock = home.read_json(self.root / "flake.lock")
        lock["nodes"]["foundation"]["locked"]["repo"] = "other"
        home.write_json(self.root / "flake.lock", lock)
        with self.assertRaisesRegex(ValueError, "another repository"):
            home.installed_info(self.root)

    def test_channel_update_builds_exact_release_and_preserves_personal_files(self):
        self.check_successful_update(True)

    def test_fixed_commit_update_remains_fixed(self):
        self.check_successful_update(False)

    def test_update_preserves_supplied_schema_three_and_capabilities(self):
        value = {**home.read_json(self.root / "profile.json"), "schema": 3,
                 "roles": ["family"], "capabilities": ["recording"], "custom": {"retain": True}}
        home.write_json(self.root / "profile.json", value)
        self.check_successful_update(True)

    def check_successful_update(self, tracking):
        if not tracking:
            (self.root / "flake.nix").write_text(home.consumer_flake(INFO, reference=INFO["rev"]))
            home.write_json(self.root / "flake.lock", home.consumer_lock(LOCK, INFO, reference=INFO["rev"]))
        candidate = {**INFO, "version": "0.3.0", "rev": "b" * 40}
        before = {name: (self.root / name).read_bytes() for name in ("profile.json", "customize.nix", "modules/local.nix")}
        def lock_update(command, **kwargs):
            stage = Path(command[-1].removeprefix("path:"))
            self.assertIn(candidate["rev"], (stage / "flake.nix").read_text())
            home.write_json(stage / "flake.lock", home.consumer_lock(LOCK, candidate, reference=candidate["rev"]))
        def build(stage):
            lock = home.read_json(stage / "flake.lock")
            reference = "latest-release" if tracking else candidate["rev"]
            self.assertIn(reference, (stage / "flake.nix").read_text())
            self.assertEqual(lock["nodes"]["foundation"]["original"], home.foundation_reference(reference))
            self.assertEqual(lock["nodes"]["foundation"]["locked"]["rev"], candidate["rev"])
            for name, contents in before.items():
                self.assertEqual((stage / name).read_bytes(), contents)
            return self.activation
        with patch.object(home, "available", return_value=(INFO, candidate, LOCK)), patch.object(home, "run", side_effect=lock_update), patch.object(home, "build", side_effect=build), patch.object(home, "provision_brew"), patch.object(home, "commit_stage") as commit:
            home.update(self.root)
            commit.assert_called_once()

    def test_migration_rebases_personal_follows_without_changing_sources(self):
        original = {"nixpkgs": {"url": "core"}, "nixpkgs-unstable": {"url": "unstable"}, "personal": {
            "url": "github:example/personal/commit",
            "inputs": {"nixpkgs": {"follows": "nixpkgs"}},
        }, "alias": {"follows": "nixpkgs-weekly"}, "unstable-alias": {"follows": "nixpkgs-unstable"}}
        extras = home.migrate_input_declarations(original)
        self.assertNotIn("nixpkgs", extras)
        self.assertNotIn("nixpkgs-unstable", extras)
        self.assertEqual(extras["personal"]["inputs"]["nixpkgs"]["follows"], "foundation/nixpkgs")
        self.assertEqual(extras["alias"]["follows"], "foundation/nixpkgs-weekly")
        self.assertEqual(extras["unstable-alias"]["follows"], "foundation/nixpkgs-unstable")
        self.assertEqual(original["personal"]["inputs"]["nixpkgs"]["follows"], "nixpkgs")
        self.assertEqual(extras["personal"]["url"], original["personal"]["url"])

    def test_concurrent_edit_prevents_installation(self):
        digest = home.tree_digest(self.root)
        stage = self.base / "stage"
        home.copy_configuration(self.root, stage)
        (self.root / "customize.nix").write_text("edited during build")
        with self.assertRaisesRegex(ValueError, "changed during"):
            home.commit_stage(self.root, stage, digest, self.activation)
        self.assertEqual((self.root / "customize.nix").read_text(), "edited during build")

    def test_personal_legacy_nixgl_pin_cannot_be_silently_adopted_as_core(self):
        original = {"nixGL": {"url": "github:nix-community/nixGL/" + "a" * 40},
                    "personal": {"url": "github:example/personal", "inputs": {"nixGL": {"follows": "nixGL"}}}}
        before = json.dumps(original, sort_keys=True)
        with self.assertRaisesRegex(ValueError, "nixGL.*personal pin"):
            home.migrate_input_declarations(original)
        self.assertEqual(json.dumps(original, sort_keys=True), before)

    def test_activation_failure_restores_files_and_previous_generation(self):
        digest = home.tree_digest(self.root)
        stage = self.base / "stage"
        home.copy_configuration(self.root, stage)
        (stage / "flake.nix").write_text("candidate")
        original = (self.root / "flake.nix").read_text()
        previous = self.base / "old-generation"
        with patch.object(home, "previous_generation", return_value=previous), patch.object(home, "run") as run:
            run.side_effect = [subprocess.CalledProcessError(1, "activate"), None]
            with self.assertRaises(subprocess.CalledProcessError):
                home.commit_stage(self.root, stage, digest, self.activation)
            self.assertEqual(run.call_args_list[-1].args[0], [str(previous / "activate")])
        self.assertEqual((self.root / "flake.nix").read_text(), original)

    def test_success_preserves_personal_git_and_espanso_module(self):
        (self.root / ".git").mkdir()
        (self.root / ".git/keep").write_text("repository metadata")
        module = '{...}: { xdg.configFile."espanso/match/private.yml".source = "private"; };'
        (self.root / "modules/local.nix").write_text(module)
        stage = self.base / "stage"
        home.copy_configuration(self.root, stage)
        digest = home.tree_digest(self.root)
        with patch.object(home, "previous_generation", return_value=None), patch.object(home, "run"), patch.dict(os.environ, XDG_CONFIG_HOME=str(self.base)):
            home.commit_stage(self.root, stage, digest, self.activation)
        self.assertEqual((self.root / ".git/keep").read_text(), "repository metadata")
        self.assertEqual((self.root / "modules/local.nix").read_text(), module)

    def test_failed_build_leaves_configuration_unchanged(self):
        digest = home.tree_digest(self.root)
        candidate = {**INFO, "version": "0.3.0", "rev": "b" * 40}
        def lock_update(command, **kwargs):
            stage = Path(command[-1].removeprefix("path:"))
            home.write_json(stage / "flake.lock", home.consumer_lock(LOCK, candidate))
        with patch.object(home, "available", return_value=(INFO, candidate, LOCK)), patch.object(home, "run", side_effect=lock_update), patch.object(home, "build", side_effect=ValueError("build failed")):
            with self.assertRaisesRegex(ValueError, "build failed"):
                home.update(self.root)
        self.assertEqual(home.tree_digest(self.root), digest)

    def test_explicit_build_budget_retains_job_core_and_swap_limits(self):
        with patch.dict(os.environ, FOUNDATION_BUILD_MEMORY_MAX="5G"), patch.object(home, "validate_staged_profile", return_value=home.read_json(self.root / "profile.json")), patch.object(home, "capture", return_value=str(self.activation)) as capture:
            self.assertEqual(home.build(self.root), self.activation)
        command = capture.call_args.args[0]
        self.assertIn("MemoryMax=5G", command)
        self.assertIn("MemorySwapMax=512M", command)
        self.assertEqual(command[command.index("--max-jobs") + 1], "1")
        self.assertEqual(command[command.index("--cores") + 1], "1")

    def test_invalid_build_budget_fails_before_evaluation(self):
        for budget in ("0G", "infinity", "-1G", "5G; anything"):
            with patch.dict(os.environ, FOUNDATION_BUILD_MEMORY_MAX=budget), patch.object(home, "capture") as capture:
                with self.assertRaisesRegex(ValueError, "positive M or G budget"):
                    home.build(self.root)
                capture.assert_not_called()

    def test_check_does_not_build_or_write(self):
        digest = home.tree_digest(self.root)
        candidate = {**INFO, "version": "0.3.0", "rev": "b" * 40}
        with patch.object(home, "available", return_value=(INFO, candidate, LOCK)), patch.object(home, "build") as build:
            home.update(self.root, check=True)
            build.assert_not_called()
        self.assertEqual(home.tree_digest(self.root), digest)

    def test_no_new_release_is_a_no_op(self):
        with patch.object(home, "published_releases", return_value=[((0, 1, 0), "v0.1.0"), ((0, 2, 0), "v0.2.0")]):
            installed, candidate, lock = home.available(self.root)
        self.assertEqual(installed, INFO)
        self.assertIsNone(candidate)

    def test_migration_rejects_modified_upstream_module(self):
        (self.root / "foundation.json").unlink()
        managed = self.root / "modules/finite.nix"
        managed.write_text("custom upstream changes")
        with self.assertRaisesRegex(ValueError, "Locally modified upstream"):
            home.migrate(self.root, INFO, LOCK)

    def test_migration_preserves_local_espanso_and_personal_input_pins(self):
        (self.root / "foundation.json").unlink()
        generated = self.root / "modules/finite.nix"
        generated.write_text("known generated module")
        personal = '{...}: { xdg.configFile."espanso/match/private.yml".source = "pinned-workstation-snapshot"; };'
        (self.root / "modules/local.nix").write_text(personal)
        (self.root / "flake.nix").write_text("{\n  outputs = inputs: {};\n}\n")
        legacy_lock = copy.deepcopy(LOCK)
        legacy_lock["nodes"]["root"]["inputs"]["personal"] = "personal"
        legacy_lock["nodes"]["personal"] = {"flake": False, "locked": {"type": "git", "rev": "personal-revision"}}
        home.write_json(self.root / "flake.lock", legacy_lock)
        fixture = self.base / "source"
        fixture.mkdir()
        home.write_json(fixture / "legacy-managed.json", {
            "files": {"modules/finite.nix": [hashlib.sha256(generated.read_bytes()).hexdigest()]},
            "outputs": [hashlib.sha256("outputs=inputs:{};}\n".strip().encode()).hexdigest()],
        })
        with patch.object(home, "source_root", return_value=fixture), patch.object(home, "capture", return_value=json.dumps({"personal": {"url": "file:///personal", "flake": False}})), patch.object(home, "build", return_value=self.activation), patch.object(home, "provision_brew"), patch.object(home, "previous_generation", return_value=None), patch.object(home, "run"), patch.dict(os.environ, XDG_CONFIG_HOME=str(self.base)):
            home.migrate(self.root, INFO, LOCK)
        self.assertEqual((self.root / "modules/local.nix").read_text(), personal)
        self.assertFalse(generated.exists())
        lock = home.read_json(self.root / "flake.lock")
        self.assertEqual(lock["nodes"]["personal"]["locked"]["rev"], "personal-revision")
        self.assertEqual(lock["nodes"]["foundation-pkgs"]["locked"], LOCK["nodes"]["pkgs"]["locked"])

    def test_default_inputs_and_modules_have_no_workstation_sources(self):
        defaults = "\n".join((ROOT / name).read_text() for name in ("flake.nix", "customize.nix", "modules/local.nix"))
        self.assertNotIn("git.vates.tech", defaults)
        self.assertNotIn("dale-express", defaults)

    def test_click_and_review_button_open_read_only_window(self):
        candidate = {**INFO, "version": "0.3.0", "rev": "b" * 40}
        with patch.dict(os.environ, XDG_STATE_HOME=str(self.base / "state")):
            for action in ("default", "review"):
                with patch.object(home, "available", return_value=(INFO, candidate, LOCK)), patch.object(home, "capture", return_value=action), patch.object(home.subprocess, "run") as run:
                    run.return_value.returncode = 0
                    home.status(self.root, notify=True)
                    self.assertEqual(run.call_args.args[0][0], "zenity")
                (self.base / "state/foundation/notified-release").unlink()

    def test_network_failure_is_visible_without_changes(self):
        digest = home.tree_digest(self.root)
        with patch.object(home, "published_releases", side_effect=OSError("network unavailable")):
            with self.assertRaises(OSError):
                home.update(self.root)
        self.assertEqual(home.tree_digest(self.root), digest)


if __name__ == "__main__":
    unittest.main()

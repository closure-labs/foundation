"""Exercise consumer locks, migrations, transactional updates and notifications."""
import copy
import contextlib
import hashlib
import importlib.util
import json
import io
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
        # These recovery/update fixtures deliberately model an existing schema-2 consumer.
        value = home.read_json(self.root / "profile.json")
        value = {key: item for key, item in value.items() if key not in ("host", "capabilities")}
        home.write_json(self.root / "profile.json", {**value, "schema": 2, "hardware": "generic-x86_64"})
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

    def test_template_copies_are_editable_without_changing_sources_or_existing_files(self):
        source = self.base / "read-only-source"
        (source / "modules").mkdir(parents=True)
        relatives = ("profile.json", "customize.nix", "modules/local.nix")
        for relative in relatives:
            path = source / relative
            path.write_text("original\n")
            path.chmod(0o444)
        output = self.base / "editable-template"
        home.make_template(source, INFO, output, LOCK)
        for relative in relatives:
            with self.subTest(relative=relative):
                destination = output / relative
                self.assertEqual(destination.stat().st_mode & 0o777, 0o644)
                destination.write_text("personal\n")
                destination.chmod(0o440)
        home.make_template(source, INFO, output, LOCK)
        for relative in relatives:
            with self.subTest(relative=relative):
                self.assertEqual((source / relative).read_text(), "original\n")
                self.assertEqual((source / relative).stat().st_mode & 0o777, 0o444)
                self.assertEqual((output / relative).read_text(), "personal\n")
                self.assertEqual((output / relative).stat().st_mode & 0o777, 0o440)

    def test_templates_preserve_dangling_personal_symlinks(self):
        for relative in ("profile.json", "customize.nix", "modules/local.nix"):
            destination = self.root / relative
            destination.unlink()
            destination.symlink_to(self.base / (destination.name + ".personal"))
        home.make_template(ROOT, INFO, self.root, LOCK)
        for relative in ("profile.json", "customize.nix", "modules/local.nix"):
            destination = self.root / relative
            target = self.base / (destination.name + ".personal")
            with self.subTest(relative=relative):
                self.assertTrue(destination.is_symlink())
                self.assertEqual(destination.readlink(), target)
                self.assertFalse(target.exists())

    def test_nh_lock_update_overrides_stale_cached_provenance_without_writes(self):
        candidate = {**INFO, "version": "0.3.0", "rev": "b" * 40}
        home.write_json(self.root / "flake.lock", home.consumer_lock(LOCK, candidate))
        before = home.tree_digest(self.root)
        with patch.object(home, "capture", return_value=json.dumps({"schema": 1, "compatibility": 1, "version": "0.3.0"})) as capture:
            self.assertEqual(home.installed_info(self.root), candidate)
        self.assertIn(candidate["rev"], capture.call_args.args[0][-1])
        self.assertEqual(home.tree_digest(self.root), before)

    def local_pin(self, **changes):
        lock = home.read_json(self.root / "flake.lock")
        source = {**{key: INFO[key] for key in ("rev", "narHash", "lastModified")},
                  "type": "git", "url": "file:///local/foundation", **changes}
        lock["nodes"]["foundation"]["locked"] = source
        lock["nodes"]["foundation"]["original"] = {"type": "git", "url": source["url"], "rev": source.get("rev")}
        home.write_json(self.root / "flake.lock", lock)
        return {"metadata": {key: INFO[key] for key in ("schema", "compatibility", "version")},
                **{key: source[key] for key in ("rev", "narHash", "lastModified")}}

    def test_local_pin_metadata_comes_from_the_locked_source_not_the_cache(self):
        selected = self.local_pin()
        selected["metadata"]["version"] = "0.3.0"
        before = home.tree_digest(self.root)
        with patch.object(home, "capture", return_value=json.dumps(selected)) as capture:
            self.assertEqual(home.installed_info(self.root), {**INFO, "version": "0.3.0"})
        command = capture.call_args.args[0]
        self.assertIn("--no-update-lock-file", command)
        self.assertIn("root.inputs.foundation", command[-1])
        self.assertIn("path:" + str(self.root), command[-1])
        self.assertNotIn("git+file:", command[-1])
        self.assertEqual(home.tree_digest(self.root), before)

    def test_local_pin_requires_explicit_revision_hash_and_local_file_url(self):
        for changes in ({"rev": None}, {"rev": "HEAD"}, {"narHash": None}, {"narHash": "bad"},
                        {"url": "git+https://example.com/foundation"}, {"url": "ssh://example.com/foundation"},
                        {"url": "file://remote/local/foundation"}, {"url": "file:relative"},
                        {"url": "file:///local/foundation?ref=main"}, {"url": "file:///local/foundation#fragment"}):
            with self.subTest(changes=changes):
                self.local_pin(**changes)
                with patch.object(home, "capture") as capture:
                    with self.assertRaises(ValueError):
                        home.installed_info(self.root)
                    capture.assert_not_called()
        self.local_pin()
        lock = home.read_json(self.root / "flake.lock")
        lock["nodes"]["foundation"]["original"].pop("rev")
        home.write_json(self.root / "flake.lock", lock)
        with patch.object(home, "capture") as capture:
            with self.assertRaisesRegex(ValueError, "explicitly pin"):
                home.installed_info(self.root)
            capture.assert_not_called()
        lock["nodes"]["foundation"]["original"]["rev"] = "b" * 40
        home.write_json(self.root / "flake.lock", lock)
        with patch.object(home, "capture") as capture:
            with self.assertRaisesRegex(ValueError, "explicitly pin"):
                home.installed_info(self.root)
            capture.assert_not_called()

    def test_local_pin_rejects_selected_source_mismatch_or_invalid_metadata(self):
        selected = self.local_pin()
        cases = [{**selected, "rev": "b" * 40}, {**selected, "narHash": "sha256-" + "B" * 43 + "="},
                 {**selected, "metadata": {**selected["metadata"], "compatibility": 2}},
                 {**selected, "metadata": {**selected["metadata"], "version": "invalid"}}]
        for value in cases:
            with self.subTest(value=value), patch.object(home, "capture", return_value=json.dumps(value)):
                with self.assertRaises(ValueError):
                    home.installed_info(self.root)

    def test_local_update_and_status_skip_release_network_and_configuration_changes(self):
        selected = self.local_pin()
        before = home.tree_digest(self.root)
        output = io.StringIO()
        with patch.object(home, "capture", return_value=json.dumps(selected)), patch.object(home, "published_releases") as releases, patch.object(home, "release_data") as release, patch.object(home, "build") as build, patch.object(home, "provision_brew") as brew, patch.object(home, "commit_stage") as commit, contextlib.redirect_stdout(output):
            self.assertEqual(home.available(self.root), (INFO, None, None))
            home.update(self.root, check=True)
            home.update(self.root)
            home.status(self.root, notify=True)
            home.status(self.root, machine=True)
        for action in (releases, release, build, brew, commit):
            action.assert_not_called()
        self.assertIn("Advance the foundation input explicitly", output.getvalue())
        self.assertIn("Published releases were not checked", output.getvalue())
        result = json.loads(output.getvalue().splitlines()[-1])
        self.assertEqual(result["source"], "local-git")
        self.assertEqual(result["update_policy"], "manual-pin")
        self.assertFalse(result["update_available"])
        self.assertEqual(home.tree_digest(self.root), before)

    def test_apply_accepts_a_local_pin_without_changing_its_declaration_or_lock(self):
        selected = self.local_pin()
        declaration = '{ inputs.foundation.url = "git+file:///local/foundation?rev=' + INFO["rev"] + '"; }\n'
        (self.root / "flake.nix").write_text(declaration)
        before = home.tree_digest(self.root)
        def build(stage):
            self.assertEqual((stage / "flake.nix").read_text(), declaration)
            self.assertEqual((stage / "flake.lock").read_bytes(), (self.root / "flake.lock").read_bytes())
            self.assertEqual(home.read_json(stage / "profile.json")["roles"], ["sales"])
            self.assertEqual(home.read_json(stage / "foundation.json"), INFO)
            return self.activation
        with patch.object(home, "capture", return_value=json.dumps(selected)), patch.object(home, "build", side_effect=build) as built, patch.object(home, "provision_brew") as brew, patch.object(home, "commit_stage") as commit:
            home.apply(self.root, roles="sales", check=True)
            built.assert_called_once()
            brew.assert_not_called(); commit.assert_not_called()
        self.assertEqual(home.tree_digest(self.root), before)

    def test_reviewed_customization_commit_preserves_personal_metadata(self):
        stage = self.base / "candidate"
        home.copy_configuration(self.root, stage)
        (stage / "customize.nix").write_text("{ /* reviewed graphical bindings */ }")
        (self.root / ".git").mkdir()
        (self.root / ".git/user-metadata").write_text("retain")
        original_module = (self.root / "modules/local.nix").read_bytes()
        with patch.object(home, "previous_generation", return_value=None), patch.dict(os.environ, XDG_CONFIG_HOME=str(self.base / "config")):
            home.commit_stage(self.root, stage, home.tree_digest(self.root), self.activation, replace_customization=True)
        self.assertEqual((self.root / "customize.nix").read_bytes(), (stage / "customize.nix").read_bytes())
        self.assertEqual((self.root / "modules/local.nix").read_bytes(), original_module)
        self.assertEqual((self.root / ".git/user-metadata").read_text(), "retain")

    def test_failed_reviewed_customization_commit_restores_original_tree(self):
        stage = self.base / "candidate"
        home.copy_configuration(self.root, stage)
        (stage / "customize.nix").write_text("{ /* reviewed graphical bindings */ }")
        home.write_json(stage / "profile.json", {**home.read_json(stage / "profile.json"), "schema": 3})
        original = home.tree_digest(self.root)
        (self.activation / "activate").write_text("#!/bin/sh\nexit 1\n")
        with patch.object(home, "previous_generation", return_value=None):
            with self.assertRaises(subprocess.CalledProcessError):
                home.commit_stage(self.root, stage, original, self.activation, replace_customization=True)
        self.assertEqual(home.tree_digest(self.root), original)

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

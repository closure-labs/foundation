"""Profile changes, stale preview guards and transactional recovery."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_home import ROOT, home, INFO, LOCK
from test_profile_classification import evaluate
from test_profile_validation import profile


def pure_preview(value, **changes):
    return evaluate(f'(import {ROOT}/lib/profile-changes.nix {{catalog = domain;}}) '
                    + home.nix_value({"profile": value, **changes}))


class ProfileChangeContract(unittest.TestCase):
    def test_packages_are_candidate_changes_and_removals_keep_the_original_source(self):
        value = {**profile(), "custom": {"keep": True}}
        result = pure_preview(value, roles=["family"], packages=[], capabilities=["recording"])
        self.assertEqual(result["source"]["packages"], ["jj", "uv"])
        self.assertEqual(result["candidate"]["packages"], [])
        self.assertEqual(result["candidate"]["custom"], value["custom"])
        self.assertIn("nix:nixpkgs:jujutsu", result["changes"]["removedDeclarations"])
        self.assertIn("nix:nixpkgs:uv", result["changes"]["removedDeclarations"])
        self.assertFalse(result["activationAllowed"])

    def test_omitted_capabilities_are_preserved_and_explicit_empty_clears_them(self):
        value = {**profile(), "schema": 3, "roles": ["family"], "capabilities": ["recording"]}
        self.assertEqual(pure_preview(value)["candidate"]["capabilities"], ["recording"])
        self.assertEqual(pure_preview(value, capabilities=[])["candidate"]["capabilities"], [])
        self.assertIn("obs", pure_preview(value, capabilities=[])["changes"]["removedApplications"])

    def test_schema_two_preview_is_rejected(self):
        with self.assertRaises(subprocess.CalledProcessError):
            pure_preview({**profile(), "schema": 2}, roles=["sales"], packages=[])


class ProfileEditor(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.root = self.base / "home-manager"
        home.make_template(ROOT, INFO, self.root, LOCK)
        self.value = {**profile(), "custom": {"retain": True}}
        home.write_json(self.root / "profile.json", self.value)
        self.source = {"path": "/nix/store/fixture-source", "rev": "a" * 40, "narHash": "fixture"}
        self.activation = self.base / "new-generation"
        self.activation.mkdir()
        (self.activation / "activate").touch()
        self.target = patch.object(home, "editor_target", side_effect=self.editor_target)
        self.target.start()
        self.addCleanup(self.target.stop)
        installed = patch.object(home, "installed_info", return_value=INFO)
        installed.start()
        self.addCleanup(installed.stop)

    def editor_target(self, stage, schema, change=None):
        value = home.read_json(stage / "profile.json")
        preview = pure_preview(value, **(change or {}))
        return {"profile": preview["source"], "preview": preview, "source": dict(self.source)}

    def preview(self, **changes):
        return home.apply(self.root, preview=True, roles="family", **changes)

    def test_preview_is_deterministic_and_has_no_live_writes_or_external_effects(self):
        before = home.tree_digest(self.root)
        with patch.object(home, "build") as build, patch.object(home, "prepare_generation") as brew, patch.object(home, "commit_stage") as commit:
            first = self.preview(capabilities="recording", packages="")
            second = self.preview(capabilities="recording", packages="")
        self.assertEqual(first, second)
        self.assertEqual(home.tree_digest(self.root), before)
        self.assertFalse((self.base / ".foundation.lock").exists())
        build.assert_not_called(); brew.assert_not_called(); commit.assert_not_called()
        self.assertIn("do not automatically import", first["summary"])

    def test_schema_two_is_rejected_before_build(self):
        value = {**self.value, "schema": 2}
        home.write_json(self.root / "profile.json", value)
        with patch.object(home, "build") as build, patch.object(home, "prepare_generation") as brew:
            with self.assertRaisesRegex(ValueError, "recreate.*schema 3"):
                home.apply(self.root, roles="family")
        build.assert_not_called(); brew.assert_not_called()
        self.assertEqual(home.read_json(self.root / "profile.json"), value)

    def test_matching_preview_builds_candidate_and_uses_existing_transaction(self):
        review = self.preview(capabilities="recording", packages="")
        def build(stage):
            self.assertEqual(home.read_json(stage / "profile.json"), review["preview"]["candidate"])
            return self.activation
        with patch.object(home, "build", side_effect=build), patch.object(home, "prepare_generation") as brew, patch.object(home, "commit_stage") as commit:
            home.apply(self.root, roles="family", packages="", capabilities="recording", approve_preview=review["approvalToken"])
        brew.assert_called_once(); commit.assert_called_once()
        self.assertEqual(commit.call_args.kwargs["expected_profile_hash"], home.profile_hash(self.root))

    def test_build_only_change_needs_no_approval_and_preserves_live_profile(self):
        before = home.tree_digest(self.root)
        with patch.object(home, "build", return_value=self.activation) as build, patch.object(home, "prepare_generation") as brew:
            home.apply(self.root, roles="family", check=True)
        build.assert_called_once(); brew.assert_not_called()
        self.assertEqual(home.tree_digest(self.root), before)

    def test_changed_selections_reject_a_previous_preview_before_build(self):
        review = self.preview(capabilities="recording")
        with patch.object(home, "build") as build:
            with self.assertRaisesRegex(ValueError, "stale"):
                home.apply(self.root, roles="family", capabilities="notes", approve_preview=review["approvalToken"])
        build.assert_not_called()

    def test_changed_profile_lock_or_personal_module_invalidates_approval(self):
        for path in ("profile.json", "flake.lock", "customize.nix"):
            review = self.preview()
            selected = self.root / path
            before = selected.read_bytes()
            selected.write_bytes(before + b"\n")
            with self.subTest(path=path), patch.object(home, "build") as build:
                with self.assertRaisesRegex(ValueError, "stale"):
                    home.apply(self.root, roles="family", approve_preview=review["approvalToken"])
                build.assert_not_called()
            selected.write_bytes(before)

    def test_preview_is_bound_to_selected_source_and_canonical_consumer_root(self):
        review = self.preview()
        self.source["path"] = "/nix/store/different-target"
        with self.assertRaisesRegex(ValueError, "stale"):
            home.apply(self.root, roles="family", approve_preview=review["approvalToken"])
        self.source["path"] = "/nix/store/fixture-source"
        other = self.base / "other-consumer"
        home.copy_configuration(self.root, other)
        with self.assertRaisesRegex(ValueError, "stale"):
            home.apply(other, roles="family", approve_preview=review["approvalToken"])

    def link_profile(self):
        linked = self.base / "private-profile.json"
        shutil.copyfile(self.root / "profile.json", linked)
        (self.root / "profile.json").unlink()
        (self.root / "profile.json").symlink_to(linked)
        return linked

    def test_changed_linked_profile_bytes_invalidate_preview_even_when_tree_is_equal(self):
        linked = self.link_profile()
        review = self.preview()
        before = home.tree_digest(self.root)
        linked.write_text(linked.read_text() + "\n")
        self.assertEqual(home.tree_digest(self.root), before)
        with patch.object(home, "build") as build:
            with self.assertRaisesRegex(ValueError, "stale"):
                home.apply(self.root, roles="family", approve_preview=review["approvalToken"])
        build.assert_not_called()

    def test_linked_profile_change_during_build_prevents_brew_and_commit(self):
        linked = self.link_profile()
        review = self.preview()
        def build(stage):
            linked.write_text(linked.read_text() + "\n")
            return self.activation
        with patch.object(home, "build", side_effect=build), patch.object(home, "prepare_generation") as brew, patch.object(home, "commit_stage") as commit:
            with self.assertRaisesRegex(ValueError, "changed during the build"):
                home.apply(self.root, roles="family", approve_preview=review["approvalToken"])
        brew.assert_not_called(); commit.assert_not_called()
        self.assertTrue((self.root / "profile.json").is_symlink())

    def test_failed_build_leaves_original_profile_and_sources_intact(self):
        review = self.preview()
        before = home.tree_digest(self.root)
        with patch.object(home, "build", side_effect=ValueError("build failed")), patch.object(home, "prepare_generation") as brew:
            with self.assertRaisesRegex(ValueError, "build failed"):
                home.apply(self.root, roles="family", approve_preview=review["approvalToken"])
        brew.assert_not_called()
        self.assertEqual(home.tree_digest(self.root), before)

    def test_failed_activation_restores_profile_and_previous_generation(self):
        self.activation_failure_restores_original()

    def test_failed_activation_restores_the_original_profile_symlink(self):
        linked = self.link_profile()
        before = linked.read_bytes()
        self.activation_failure_restores_original()
        self.assertTrue((self.root / "profile.json").is_symlink())
        self.assertEqual((self.root / "profile.json").readlink(), linked)
        self.assertEqual(linked.read_bytes(), before)

    def activation_failure_restores_original(self):
        review = self.preview()
        before = home.tree_digest(self.root)
        previous = self.base / "old-generation"
        previous.mkdir(); (previous / "activate").touch()
        def activate(command, **kwargs):
            if command == [str(self.activation / "activate")]:
                self.assertEqual(home.read_json(self.root / "profile.json")["schema"], 3)
                raise subprocess.CalledProcessError(1, command)
        with patch.object(home, "build", return_value=self.activation), patch.object(home, "prepare_generation"), patch.object(home, "previous_generation", return_value=previous), patch.object(home, "run", side_effect=activate) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                home.apply(self.root, roles="family", approve_preview=review["approvalToken"])
        self.assertEqual(home.tree_digest(self.root), before)
        self.assertEqual(home.read_json(self.root / "profile.json")["schema"], 3)
        self.assertEqual(run.call_args.args[0], [str(previous / "activate")])

    def test_successful_change_backs_up_profile_and_updates_the_finite_selection(self):
        review = self.preview()
        state = self.base / "configuration"
        with patch.object(home, "build", return_value=self.activation), patch.object(home, "prepare_generation"), patch.object(home, "previous_generation", return_value=None), patch.object(home, "run"), patch.dict(os.environ, XDG_CONFIG_HOME=str(state)):
            home.apply(self.root, roles="family", approve_preview=review["approvalToken"])
        self.assertEqual(home.read_json(self.root / "profile.json"), review["preview"]["candidate"])
        self.assertEqual(home.read_json(state / "finite/profile.json"), review["preview"]["candidate"])
        backups = list(self.base.glob("home-manager.previous.*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(home.read_json(backups[0] / "profile.json"), self.value)

    def test_malformed_input_is_rejected_without_target_queries_or_live_changes(self):
        for value in ([], None, {"schema": True}, {"schema": 2}, {"schema": 4}):
            home.write_json(self.root / "profile.json", value)
            before = home.tree_digest(self.root)
            with patch.object(home, "capture") as capture:
                with self.assertRaises(ValueError):
                    home.read_editor(self.root, )
                capture.assert_not_called()
            self.assertEqual(home.tree_digest(self.root), before)


class EditorNegotiation(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.stage = Path(self.directory.name)
        self.value = profile()
        home.write_json(self.stage / "profile.json", self.value)
        self.data = {"hasNormalizer": True, "profile": self.value, "catalog": evaluate("project domain"),
                     "capabilities": home.profile_capabilities(), "editorSchema": 1, "editorCatalog": evaluate("project domain")}

    def test_running_reader_support_alone_does_not_imply_editing(self):
        reader = {key: value for key, value in home.profile_capabilities().items() if key != "editSchemas"}
        with patch.object(home, "profile_capabilities", return_value=reader), patch.object(home, "capture") as capture:
            with self.assertRaisesRegex(ValueError, "installed.*editing"):
                home.editor_target(self.stage, 3)
            capture.assert_not_called()

    def test_target_reader_support_alone_does_not_imply_editing(self):
        data = {**self.data, "capabilities": {key: value for key, value in self.data["capabilities"].items() if key != "editSchemas"}}
        with patch.object(home, "capture", return_value=json.dumps(data)), patch.object(home, "validate_runtime_profile"):
            with self.assertRaisesRegex(ValueError, "does not advertise"):
                home.editor_target(self.stage, 3)

    def test_target_future_editor_version_is_rejected(self):
        data = {**self.data, "editorSchema": 2}
        with patch.object(home, "capture", return_value=json.dumps(data)), patch.object(home, "validate_runtime_profile"):
            with self.assertRaisesRegex(ValueError, "preview API"):
                home.editor_target(self.stage, 3, {})


if __name__ == "__main__":
    unittest.main()

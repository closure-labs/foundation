"""Exercise consumer locks, migrations, transactional updates and notifications."""
import copy
import contextlib
import hashlib
import importlib.util
import json
import io
import os
import signal
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


class MainSourceResolutionTests(unittest.TestCase):
    def setUp(self):
        self.resolved = {**home.foundation_reference("main"),
                         **{key: INFO[key] for key in ("rev", "narHash", "lastModified")}}
        self.selected = {"metadata": {key: INFO[key] for key in ("schema", "compatibility", "version")},
                         "lock": LOCK,
                         **{key: INFO[key] for key in ("rev", "narHash", "lastModified")}}
        self.evidence = {"runId": 1, "runAttempt": 1}

    def test_omitted_metadata_hash_and_timestamp_use_only_qualified_immutable_source(self):
        for omitted in ((), ("narHash",), ("lastModified",), ("narHash", "lastModified")):
            resolved = {key: value for key, value in self.resolved.items() if key not in omitted}
            with self.subTest(omitted=omitted), patch.object(home, "capture", side_effect=[
                    json.dumps({"locked": resolved}), json.dumps(self.selected)]) as capture, \
                    patch.object(home, "require_main_ci", return_value=self.evidence) as ci:
                self.assertEqual(home.main_data(), ({**INFO, "upstreamCI": self.evidence}, LOCK))
                ci.assert_called_once_with(INFO["rev"])
                self.assertIn("--refresh", capture.call_args_list[0].args[0])
                expression = capture.call_args_list[1].args[0][-1]
                self.assertIn(f'github:{home.REPOSITORY}/{INFO["rev"]}', expression)
                self.assertNotIn(f'github:{home.REPOSITORY}/main', expression)

    def test_supplied_malformed_metadata_is_rejected_before_ci_or_evaluation(self):
        cases = [{"narHash": value} for value in (None, "", "bad", 42)]
        cases += [{"owner": "attacker"}, {"repo": "other"}, {"type": "git"}, {"rev": "main"},
                  {"lastModified": None}, {"lastModified": True}, {"lastModified": -1}]
        for changes in cases:
            with self.subTest(changes=changes), patch.object(home, "capture", return_value=json.dumps(
                    {"locked": {**self.resolved, **changes}})) as capture, \
                    patch.object(home, "require_main_ci") as ci:
                with self.assertRaisesRegex(ValueError, "immutable Foundation source"):
                    home.main_data()
                self.assertEqual(capture.call_count, 1)
                ci.assert_not_called()

    def test_immutable_evaluation_must_match_supplied_source_identity(self):
        for changes in ({"rev": "b" * 40}, {"narHash": "sha256-" + "B" * 43 + "="},
                        {"lastModified": 2}):
            with self.subTest(changes=changes), patch.object(home, "capture", side_effect=[
                    json.dumps({"locked": self.resolved}), json.dumps({**self.selected, **changes})]), \
                    patch.object(home, "require_main_ci", return_value=self.evidence):
                with self.assertRaisesRegex(ValueError, "differs from the resolved main source"):
                    home.main_data()

    def test_omitted_metadata_never_allows_invalid_evaluated_source_info(self):
        resolved = {key: value for key, value in self.resolved.items()
                    if key not in ("narHash", "lastModified")}
        cases = [{"narHash": value} for value in (None, "", "bad", 42)]
        cases += [{"lastModified": value} for value in (None, True, -1, "1")]
        for changes in cases:
            with self.subTest(changes=changes), patch.object(home, "capture", side_effect=[
                    json.dumps({"locked": resolved}), json.dumps({**self.selected, **changes})]), \
                    patch.object(home, "require_main_ci", return_value=self.evidence):
                with self.assertRaisesRegex(ValueError, "differs from the resolved main source"):
                    home.main_data()

    def test_unqualified_main_is_never_evaluated(self):
        resolved = {key: value for key, value in self.resolved.items() if key != "narHash"}
        with patch.object(home, "capture", return_value=json.dumps({"locked": resolved})) as capture, \
                patch.object(home, "require_main_ci", side_effect=ValueError("CI pending")):
            with self.assertRaisesRegex(ValueError, "CI pending"):
                home.main_data()
            self.assertEqual(capture.call_count, 1)


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
        with self.assertRaisesRegex(ValueError, "committed source lock"):
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
        self.assertIn("/main", text)
        self.assertEqual(lock["nodes"]["foundation"]["original"]["ref"], "main")
        self.assertEqual(lock["nodes"]["foundation"]["locked"]["rev"], INFO["rev"])
        self.assertEqual(len(home.REFERENCE.findall((ROOT / "templates/default/flake.nix").read_text())), 1)

    def test_template_copies_are_editable_without_changing_sources_or_existing_files(self):
        source = self.base / "read-only-source"
        (source / "modules").mkdir(parents=True)
        (source / "templates/default").mkdir(parents=True)
        relatives = ("profile.json", "customize.nix", "modules/local.nix")
        sources = {relative: source / ("templates/default/customize.nix" if relative == "customize.nix" else relative)
                   for relative in relatives}
        for relative in relatives:
            path = sources[relative]
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
                self.assertEqual(sources[relative].read_text(), "original\n")
                self.assertEqual(sources[relative].stat().st_mode & 0o777, 0o444)
                self.assertEqual((output / relative).read_text(), "personal\n")
                self.assertEqual((output / relative).stat().st_mode & 0o777, 0o440)

    def test_new_customization_uses_the_public_policy_aware_template(self):
        expected = (ROOT / "templates/default/customize.nix").read_text()
        self.assertEqual((self.root / "customize.nix").read_text(), expected)
        self.assertIn("foundationPackageSets.nixpkgs-weekly", expected)
        self.assertNotIn("legacyPackages", expected)

    def test_helper_bundle_retains_only_the_required_customization_template(self):
        # This store-copy-only evaluation needs no Nixpkgs, builds or flake fetches.
        # Keep it in fixtures so even focused helper edits check the actual bundle.
        expression = 'let source = builtins.toPath ' + home.nix_value(str(ROOT)) + '; in toString (import (source + "/lib/helper-source.nix") source)'
        helper = Path(json.loads(subprocess.check_output([
            "nix-instantiate", "--eval", "--read-write-mode", "--strict", "--json", "--expr", expression,
        ], text=True)))
        self.assertEqual(sorted(path.name for path in (helper / "templates/default").iterdir()), ["customize.nix"])
        output = self.base / "packaged-template"
        home.make_template(helper, INFO, output, LOCK)
        self.assertEqual((output / "customize.nix").read_bytes(),
                         (ROOT / "templates/default/customize.nix").read_bytes())

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
        with patch.object(home, "capture", return_value=json.dumps(selected)), patch.object(home, "github_api") as releases, patch.object(home, "main_data") as release, patch.object(home, "build") as build, patch.object(home, "prepare_generation") as brew, patch.object(home, "commit_stage") as commit, contextlib.redirect_stdout(output):
            self.assertEqual(home.available(self.root), (INFO, None, None))
            home.update(self.root, check=True)
            home.update(self.root)
            home.status(self.root, notify=True)
            home.status(self.root, machine=True)
        for action in (releases, release, build, brew, commit):
            action.assert_not_called()
        self.assertIn("Advance the foundation input explicitly", output.getvalue())
        self.assertIn("Upstream main was not checked", output.getvalue())
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
        candidate = {**home.read_json(self.root / "profile.json"), "roles": ["sales"]}
        preview = {"preview": {"status": "preview", "candidate": candidate}}
        with patch.object(home, "prepare_profile_change", return_value=preview), patch.object(home, "capture", return_value=json.dumps(selected)), patch.object(home, "build", side_effect=build) as built, patch.object(home, "prepare_generation") as brew, patch.object(home, "commit_stage") as commit:
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

    def test_legacy_channel_migrates_to_main_on_explicit_update(self):
        (self.root / "flake.nix").write_text(home.consumer_flake(INFO, reference="latest-release"))
        home.write_json(self.root / "flake.lock", home.consumer_lock(LOCK, INFO, reference="latest-release"))
        self.check_successful_update(True)

    def test_main_race_or_wrong_original_never_builds_or_changes_live_tree(self):
        candidate = {**INFO, "rev": "b" * 40}
        digest = home.tree_digest(self.root)
        for wrong_original in (False, True):
            def lock_update(command, **kwargs):
                stage = Path(command[-1].removeprefix("path:"))
                value = candidate if wrong_original else {**candidate, "rev": "c" * 40}
                reference = candidate["rev"] if wrong_original else "main"
                home.write_json(stage / "flake.lock", home.consumer_lock(LOCK, value, reference=reference))
            with patch.object(home, "available", return_value=(INFO, candidate, LOCK)), patch.object(home, "run", side_effect=lock_update), patch.object(home, "build") as build, patch.object(home, "commit_stage") as commit:
                with self.assertRaises(ValueError): home.update(self.root)
                build.assert_not_called()
                commit.assert_not_called()
            self.assertEqual(home.tree_digest(self.root), digest)

    def test_ci_change_after_build_or_preparation_aborts_before_commit(self):
        candidate = {**INFO, "rev": "b" * 40, "upstreamCI": {"runId": 1, "runAttempt": 1}}
        digest = home.tree_digest(self.root)
        def lock_update(command, **kwargs):
            stage = Path(command[-1].removeprefix("path:"))
            home.write_json(stage / "flake.lock", home.consumer_lock(LOCK, candidate))
        for proof in ([ValueError("changed")], [None, ValueError("changed")]):
            with patch.object(home, "available", return_value=(INFO, candidate, LOCK)), patch.object(home, "run", side_effect=lock_update), patch.object(home, "build", return_value=self.activation) as build, patch.object(home, "revalidate_candidate", side_effect=proof), patch.object(home, "prepare_generation") as prepare, patch.object(home, "commit_stage") as commit:
                with self.assertRaisesRegex(ValueError, "changed"): home.update(self.root)
                build.assert_called_once()
                self.assertEqual(prepare.call_count, len(proof) - 1)
                commit.assert_not_called()
            self.assertEqual(home.tree_digest(self.root), digest)

    def test_preparation_failure_preserves_live_consumer_and_does_not_activate(self):
        candidate = {**INFO, "rev": "b" * 40}
        digest = home.tree_digest(self.root)
        def lock_update(command, **kwargs):
            stage = Path(command[-1].removeprefix("path:"))
            home.write_json(stage / "flake.lock", home.consumer_lock(LOCK, candidate))
        failure = subprocess.CalledProcessError(9, ["foundation-prepare"])
        with patch.object(home, "available", return_value=(INFO, candidate, LOCK)), \
                patch.object(home, "run", side_effect=lock_update), \
                patch.object(home, "build", return_value=self.activation), \
                patch.object(home, "revalidate_candidate"), \
                patch.object(home, "prepare_generation", side_effect=failure), \
                patch.object(home, "commit_stage") as commit:
            with self.assertRaises(subprocess.CalledProcessError):
                home.update(self.root)
            commit.assert_not_called()
        self.assertEqual(home.tree_digest(self.root), digest)

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
            reference = "main" if tracking else candidate["rev"]
            self.assertIn(reference, (stage / "flake.nix").read_text())
            home.write_json(stage / "flake.lock", home.consumer_lock(LOCK, candidate, reference=reference))
        def build(stage):
            lock = home.read_json(stage / "flake.lock")
            reference = "main" if tracking else candidate["rev"]
            self.assertIn(reference, (stage / "flake.nix").read_text())
            self.assertEqual(lock["nodes"]["foundation"]["original"], home.foundation_reference(reference))
            self.assertEqual(lock["nodes"]["foundation"]["locked"]["rev"], candidate["rev"])
            for name, contents in before.items():
                self.assertEqual((stage / name).read_bytes(), contents)
            return self.activation
        with patch.object(home, "available", return_value=(INFO, candidate, LOCK)), patch.object(home, "run", side_effect=lock_update), patch.object(home, "build", side_effect=build), patch.object(home, "prepare_generation"), patch.object(home, "revalidate_candidate") as revalidate, patch.object(home, "commit_stage") as commit:
            home.update(self.root)
            commit.assert_called_once()
            self.assertEqual(revalidate.call_count, 2)

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

    def test_default_build_budget_supports_full_schema_three_profiles(self):
        with patch.dict(os.environ), patch.object(home, "validate_staged_profile", return_value=home.read_json(self.root / "profile.json")), patch.object(home, "capture_build", return_value=str(self.activation)) as capture:
            os.environ.pop("FOUNDATION_BUILD_MEMORY_MAX", None)
            self.assertEqual(home.build(self.root), self.activation)
        command = capture.call_args.args[0]
        self.assertIn("MemoryMax=5G", command)
        self.assertIn("CPUQuota=100%", command)
        self.assertIn("MemorySwapMax=512M", command)
        self.assertEqual(command[command.index("--max-jobs") + 1], "1")
        self.assertEqual(command[command.index("--cores") + 1], "1")

    def test_explicit_build_budget_retains_job_core_and_swap_limits(self):
        for budget in ("6G", "4096M"):
            with self.subTest(budget=budget), patch.dict(os.environ, FOUNDATION_BUILD_MEMORY_MAX=budget), patch.object(home, "validate_staged_profile", return_value=home.read_json(self.root / "profile.json")), patch.object(home, "capture_build", return_value=str(self.activation)) as capture:
                self.assertEqual(home.build(self.root), self.activation)
            command = capture.call_args.args[0]
            self.assertIn("MemoryMax=" + budget, command)
            self.assertIn("CPUQuota=100%", command)
            self.assertIn("MemorySwapMax=512M", command)
            self.assertEqual(command[command.index("--max-jobs") + 1], "1")
            self.assertEqual(command[command.index("--cores") + 1], "1")

    def test_killed_build_reports_used_budget_without_retrying(self):
        failure = subprocess.CalledProcessError(-signal.SIGKILL, ["nix", "build"])
        with patch.dict(os.environ, FOUNDATION_BUILD_MEMORY_MAX="4096M"), patch.object(home, "validate_staged_profile", return_value=home.read_json(self.root / "profile.json")), patch.object(home, "capture_build", side_effect=failure) as capture:
            with self.assertRaisesRegex(ValueError, "SIGKILL.*MemoryMax=4096M") as raised:
                home.build(self.root)
        self.assertIs(raised.exception.__cause__, failure)
        self.assertIn("FOUNDATION_BUILD_MEMORY_MAX", str(raised.exception))
        self.assertIn("journal", str(raised.exception))
        capture.assert_called_once()

    def test_other_build_failures_keep_their_original_error(self):
        for code in (1, 137, -signal.SIGTERM, -signal.SIGINT):
            failure = subprocess.CalledProcessError(code, ["nix", "build"])
            with self.subTest(code=code), patch.object(home, "validate_staged_profile", return_value=home.read_json(self.root / "profile.json")), patch.object(home, "capture_build", side_effect=failure) as capture:
                with self.assertRaises(subprocess.CalledProcessError) as raised:
                    home.build(self.root)
                self.assertIs(raised.exception, failure)
                capture.assert_called_once()

    def test_killed_update_build_keeps_live_configuration_and_skips_provisioning(self):
        digest = home.tree_digest(self.root)
        candidate = {**INFO, "version": "0.3.0", "rev": "b" * 40}
        def lock_update(command, **kwargs):
            stage = Path(command[-1].removeprefix("path:"))
            home.write_json(stage / "flake.lock", home.consumer_lock(LOCK, candidate))
        failure = subprocess.CalledProcessError(-signal.SIGKILL, ["nix", "build"])
        with patch.object(home, "available", return_value=(INFO, candidate, LOCK)), patch.object(home, "run", side_effect=lock_update), patch.object(home, "validate_staged_profile", return_value=home.read_json(self.root / "profile.json")), patch.object(home, "capture_build", side_effect=failure) as capture, patch.object(home, "prepare_generation") as brew, patch.object(home, "commit_stage") as commit:
            with self.assertRaisesRegex(ValueError, "SIGKILL"):
                home.update(self.root)
            capture.assert_called_once()
            brew.assert_not_called()
            commit.assert_not_called()
        self.assertEqual(home.tree_digest(self.root), digest)

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
        with patch.object(home, "main_data", return_value=(INFO, LOCK)):
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
        self.check_migration()

    def test_migration_ci_change_after_build_keeps_live_tree(self):
        self.check_migration(stale=True)

    def check_migration(self, stale=False):
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
        with patch.object(home, "source_root", return_value=fixture), patch.object(home, "capture", return_value=json.dumps({"personal": {"url": "file:///personal", "flake": False}})), patch.object(home, "build", return_value=self.activation), patch.object(home, "prepare_generation"), patch.object(home, "previous_generation", return_value=None), patch.object(home, "revalidate_candidate") as revalidate, patch.object(home, "run"), patch.dict(os.environ, XDG_CONFIG_HOME=str(self.base)):
            if stale:
                digest = home.tree_digest(self.root)
                revalidate.side_effect = ValueError("CI proof changed")
                with patch.object(home, "commit_stage") as commit, patch.object(home, "prepare_generation") as prepare:
                    with self.assertRaisesRegex(ValueError, "CI proof changed"):
                        home.migrate(self.root, INFO, LOCK)
                    prepare.assert_not_called()
                    commit.assert_not_called()
                self.assertEqual(home.tree_digest(self.root), digest)
                return
            home.migrate(self.root, INFO, LOCK)
            self.assertEqual(revalidate.call_count, 2)
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
        with patch.object(home, "main_data", side_effect=OSError("network unavailable")):
            with self.assertRaises(OSError):
                home.update(self.root)
        self.assertEqual(home.tree_digest(self.root), digest)


if __name__ == "__main__":
    unittest.main()

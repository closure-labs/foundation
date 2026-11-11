"""Structural normalization and staged revision validation contracts."""
import copy
import json
import os
import pwd
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_home import home, INFO, LOCK, ROOT
from test_profile_classification import evaluate


def profile():
    return {"schema": 3, "foundation": "bluefin", "hardware": "generic-x86_64",
            "roles": ["it", "developer"], "packages": ["uv", "jj"], "capabilities": [],
            "identity": {"username": pwd.getpwuid(os.getuid()).pw_name,
                         "homeDirectory": str(Path.home())}}


class NormalizationTests(unittest.TestCase):
    def normalize(self, value, check=True):
        encoded = home.nix_value(json.dumps(value))
        return evaluate(f'(import {ROOT}/lib/normalize-profile.nix {{ catalog = domain; }}) '
                        f'(builtins.fromJSON {encoded})', check=check)

    def test_canonical_order_and_unknown_fields_are_preserved(self):
        value = profile()
        value["local"] = {"literal": "${untouched}", "enabled": True}
        value["identity"]["extra"] = "preserve"
        expected = copy.deepcopy(value)
        expected["host"] = evaluate(f'(import {ROOT}/lib/hosts.nix).defaults')
        expected.update(roles=["developer", "it"], packages=["jj", "uv"])
        self.assertEqual(self.normalize(value), expected)
        self.assertEqual(self.normalize(expected), expected)

    def test_empty_selections_are_valid(self):
        value = {**profile(), "roles": [], "packages": []}
        self.assertEqual(self.normalize(value), {**value, "host": evaluate(f'(import {ROOT}/lib/hosts.nix).defaults')})

    def test_malformed_or_unsupported_profiles_fail_clearly(self):
        cases = [None, [], {}, *({**profile(), **change} for change in (
            {"schema": 1}, {"schema": 2}, {"schema": 4}, {"schema": True}, {"schema": 2.0}, {"roles": "it"},
            {"roles": [["it"]]}, {"roles": ["it", "it"]}, {"roles": ["missing"]},
            {"packages": [None]}, {"packages": ["uv", "uv"]}, {"packages": ["missing"]},
            {"foundation": []}, {"hardware": "missing"}, {"identity": None},
            {"identity": {"username": "bad user", "homeDirectory": "/home/test"}},
            {"identity": {"username": "test", "homeDirectory": "/"}},
            {"identity": {"username": "test", "homeDirectory": 5}},
        ))]
        for value in cases:
            with self.subTest(value=value):
                result = self.normalize(value, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertRegex(result.stderr, "Invalid Foundation (profile|host)")

    def test_equal_order_uses_name_as_tiebreaker(self):
        encoded = home.nix_value(json.dumps(profile()))
        result = evaluate(f'''(import {ROOT}/lib/normalize-profile.nix {{
          catalog = domain // {{ packagesByName = builtins.mapAttrs (_: package: package // {{ order = 1; }}) domain.packagesByName; }};
        }}) (builtins.fromJSON {encoded})''')
        self.assertEqual(result["packages"], ["jj", "uv"])


class StagedValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = evaluate("project domain")

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.stage = self.base / "stage-${literal}"
        self.stage.mkdir()
        self.value = profile()
        home.write_json(self.stage / "profile.json", self.value)
        self.running = self.base / "running.json"
        self.env = patch.dict(os.environ, FINITE_RUNNING_PROFILE_PATH=str(self.running),
                              FINITE_FOUNDATION_CATALOG="/caller/stale/catalog.json")
        self.env.start()
        self.addCleanup(self.env.stop)

    def payload(self, normalizer=True, value=None, catalog=None):
        return json.dumps({"hasNormalizer": normalizer,
                           "profile": self.value if value is None else value,
                           "catalog": self.catalog if catalog is None else catalog,
                           "capabilities": home.profile_capabilities()})

    def test_target_normalizer_and_catalog_override_caller(self):
        normalized = {**self.value, "roles": ["developer", "it"], "packages": ["jj", "uv"]}
        with patch.object(home, "capture", return_value=self.payload(value=normalized)) as capture:
            self.assertEqual(home.validate_staged_profile(self.stage), normalized)
        command = capture.call_args.args[0]
        self.assertIn("--no-update-lock-file", command)
        expression = command[-1]
        self.assertIn("root.inputs.foundation or root", expression)
        self.assertIn("target.lib.normalizeProfile", expression)
        self.assertIn("target.lib.homeCatalog", expression)
        self.assertIn("%24%7Bliteral%7D", expression)
        self.assertNotIn("${literal}", expression)
        self.assertNotIn("/caller/stale", expression)

    def test_target_without_normalizer_is_rejected(self):
        with patch.object(home, "capture", return_value=self.payload(False)), patch.object(home, "validate_runtime_profile") as runtime:
            with self.assertRaisesRegex(ValueError, "normalizer; update Foundation"):
                home.validate_staged_profile(self.stage)
            runtime.assert_not_called()

    def test_target_evaluation_failure_never_falls_back(self):
        failure = subprocess.CalledProcessError(1, "nix eval")
        with patch.object(home, "capture", side_effect=failure) as capture:
            with self.assertRaises(subprocess.CalledProcessError):
                home.validate_staged_profile(self.stage)
            self.assertEqual(capture.call_count, 1)

    def test_runtime_identity_and_image_checks_remain_required(self):
        cases = [({**self.value, "identity": {"username": "other-user", "homeDirectory": str(Path.home())}}, None),
                 ({**self.value, "identity": {**self.value["identity"], "homeDirectory": "/wrong/home"}}, None),
                 (self.value, {"foundation": "bluefin-dx", "hardware": "generic-x86_64"}),
                 (self.value, {"foundation": "bluefin", "hardware": "unsupported"})]
        for value, running in cases:
            with self.subTest(value=value, running=running):
                self.running.unlink(missing_ok=True)
                if running:
                    home.write_json(self.running, running)
                with patch.object(home, "capture", return_value=self.payload(value=value)):
                    with self.assertRaises(ValueError):
                        home.validate_staged_profile(self.stage)

    def test_schema_two_is_rejected_before_target_evaluation_without_writes(self):
        home.write_json(self.stage / "profile.json", {**self.value, "schema": 2})
        before = home.tree_digest(self.stage)
        with patch.object(home, "capture") as capture:
            with self.assertRaisesRegex(ValueError, "schema.*recreate.*schema 3"):
                home.validate_staged_profile(self.stage)
            capture.assert_not_called()
        self.assertEqual(home.tree_digest(self.stage), before)

    def test_build_persists_normalization_before_nix_build(self):
        normalized = {**self.value, "roles": ["developer", "it"], "packages": ["jj", "uv"]}
        activation = self.base / "generation"
        activation.mkdir()
        (activation / "activate").touch()
        def capture(command):
            self.assertEqual(home.read_json(self.stage / "profile.json"), normalized)
            return str(activation)
        with patch.object(home, "validate_staged_profile", return_value=normalized), patch.object(home, "capture_build", side_effect=capture):
            self.assertEqual(home.build(self.stage), activation)

    def test_build_preserves_bytes_when_profile_is_already_normalized(self):
        self.stage.joinpath("profile.json").write_text(json.dumps(self.value, separators=(",", ":")))
        before = self.stage.joinpath("profile.json").read_bytes()
        with patch.object(home, "validate_staged_profile", return_value=self.value), patch.object(home, "capture_build", side_effect=ValueError("stop after validation")):
            with self.assertRaisesRegex(ValueError, "stop after validation"):
                home.build(self.stage)
        self.assertEqual(self.stage.joinpath("profile.json").read_bytes(), before)

    def test_failed_build_cannot_write_through_a_copied_profile_symlink(self):
        linked = self.base / "live-profile.json"
        home.write_json(linked, self.value)
        before = linked.read_bytes()
        self.stage.joinpath("profile.json").unlink()
        self.stage.joinpath("profile.json").symlink_to(linked)
        normalized = {**self.value, "roles": ["developer", "it"], "packages": ["jj", "uv"]}
        with patch.object(home, "validate_staged_profile", return_value=normalized), patch.object(home, "capture_build", side_effect=ValueError("build failed")):
            with self.assertRaisesRegex(ValueError, "build failed"):
                home.build(self.stage)
        self.assertEqual(linked.read_bytes(), before)
        self.assertFalse(self.stage.joinpath("profile.json").is_symlink())
        self.assertEqual(home.read_json(self.stage / "profile.json"), normalized)

    def test_initialize_preserves_schema_three_fields(self):
        value = {**self.value, "extra": "keep", "capabilities": ["recording"]}
        value["identity"] = {**value["identity"], "extra": "keep identity"}
        def build(stage):
            self.assertEqual(home.read_json(stage / "profile.json"), value)
        metadata = self.base / "metadata.json"
        home.write_json(metadata, INFO)
        with patch.dict(os.environ, FINITE_FOUNDATION_METADATA=str(metadata)), patch.object(home, "capture", return_value=json.dumps(value)), patch.object(home, "build", side_effect=build) as build_mock:
            root = self.base / "new-home"
            home.initialize(root, self.base / "seed.yaml", check=True)
            build_mock.assert_called_once()
            self.assertFalse(root.exists())

    def test_initialize_rejects_unknown_schema_before_creating_stage(self):
        for schema in (None, True, 0, 1, 2, 4, "2"):
            with self.subTest(schema=schema), patch.object(home, "capture", return_value=json.dumps({**self.value, "schema": schema})), patch.object(home, "make_template") as template:
                with self.assertRaisesRegex(ValueError, "Unsupported profile schema"):
                    home.initialize(self.base / "new-home", self.base / "seed.yaml", check=True)
                template.assert_not_called()

    def test_apply_validation_failure_preserves_live_tree(self):
        root = self.base / "live"
        home.make_template(ROOT, INFO, root, LOCK)
        home.write_json(root / "profile.json", self.value)
        before = home.tree_digest(root)
        with patch.object(home, "installed_info", return_value=INFO), patch.object(home, "prepare_profile_change", side_effect=ValueError("target rejected")), patch.object(home, "prepare_generation") as brew, patch.object(home, "commit_stage") as commit:
            with self.assertRaisesRegex(ValueError, "target rejected"):
                home.apply(root, roles="missing")
            brew.assert_not_called()
            commit.assert_not_called()
        self.assertEqual(home.tree_digest(root), before)

    def test_failed_apply_preserves_a_linked_live_profile(self):
        root = self.base / "live"
        home.make_template(ROOT, INFO, root, LOCK)
        linked = self.base / "live-profile.json"
        home.write_json(linked, self.value)
        root.joinpath("profile.json").unlink()
        root.joinpath("profile.json").symlink_to(linked)
        before = linked.read_bytes()
        digest = home.tree_digest(root)
        with patch.object(home, "installed_info", return_value=INFO), patch.object(home, "prepare_profile_change", side_effect=ValueError("target rejected")):
            with self.assertRaisesRegex(ValueError, "target rejected"):
                home.apply(root, roles="missing")
        self.assertEqual(linked.read_bytes(), before)
        self.assertTrue(root.joinpath("profile.json").is_symlink())
        self.assertEqual(home.tree_digest(root), digest)

    def test_apply_retains_schema_three_capabilities_and_custom_fields(self):
        root = self.base / "live-three"
        home.make_template(ROOT, INFO, root, LOCK)
        value = {**self.value, "schema": 3, "roles": ["family"],
                 "capabilities": ["recording"], "custom": {"retain": True}}
        home.write_json(root / "profile.json", value)
        before = home.tree_digest(root)
        def check_stage(stage):
            self.assertEqual(home.read_json(stage / "profile.json"), {**value, "roles": ["media"], "packages": [],
                "host": evaluate(f'(import {ROOT}/lib/hosts.nix).defaults')})
        change = {"profile": value, "roles": ["media"], "packages": []}
        preview = evaluate(f'(import {ROOT}/lib/profile-changes.nix {{catalog = domain;}}) {home.nix_value(change)}')
        with patch.object(home, "prepare_profile_change", return_value={"preview": preview}), patch.object(home, "installed_info", return_value=INFO), patch.object(home, "build", side_effect=check_stage) as build, patch.object(home, "prepare_generation") as brew:
            home.apply(root, roles="media", packages="", check=True)
            build.assert_called_once()
            brew.assert_not_called()
        self.assertEqual(home.tree_digest(root), before)


if __name__ == "__main__":
    unittest.main()

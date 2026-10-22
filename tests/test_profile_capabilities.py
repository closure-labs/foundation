"""Capabilities describe actual readers without enabling a new writer."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_home import ROOT, home
from test_profile_classification import evaluate
from test_profile_validation import profile


class CapabilityTests(unittest.TestCase):
    def test_catalog_and_helper_share_current_capabilities(self):
        capabilities = home.profile_capabilities()
        self.assertEqual(capabilities, evaluate("(project domain).profileCapabilities"))
        self.assertEqual(capabilities["initializeSchemas"], [1, 2, 3])
        self.assertEqual(capabilities["normalizeSchemas"], [2, 3])
        self.assertEqual(capabilities["writeSchema"], 3)
        self.assertEqual(capabilities["editSchemas"], [2, 3])
        self.assertEqual(capabilities["catalogSchemas"], [3])

    def test_read_only_cli_query_ignores_source_and_profile_overrides(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run([sys.executable, str(ROOT / "scripts/home.py"), "init", "--capabilities"],
                                    cwd=temporary, text=True, capture_output=True,
                                    env=dict(os.environ, FINITE_FOUNDATION_SOURCE="/missing-source",
                                             FINITE_HOME_FLAKE_PATH=str(Path(temporary) / "untouched")))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), home.profile_capabilities())
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_explicit_malformed_descriptors_fail(self):
        valid = home.profile_capabilities()
        for value in (None, {}, {**valid, "schema": True}, {**valid, "writeSchema": 4},
                      {**valid, "normalizeSchemas": [True]}, {**valid, "initializeSchemas": [1, 1]},
                      {**valid, "catalogSchemas": "3"},
                      *({**valid, "editSchemas": item} for item in (None, [], [True], [2, 2], [4]))):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "capabilit"):
                home.validate_capabilities(value)

    def test_running_helper_rejects_new_profile_schema_before_target_evaluation(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            home.write_json(stage / "profile.json", {**profile(), "schema": 4})
            with patch.object(home, "capture") as capture:
                with self.assertRaisesRegex(ValueError, "helper.*schema"):
                    home.validate_staged_profile(stage)
                capture.assert_not_called()

    def test_selected_target_capabilities_must_accept_profile_and_catalog(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            value = profile()
            home.write_json(stage / "profile.json", value)
            catalog = evaluate("project domain")
            capabilities = home.profile_capabilities()
            candidates = [None, {**capabilities, "normalizeSchemas": [3], "writeSchema": 3, "initializeSchemas": [3]},
                          {**capabilities, "catalogSchemas": [4]}]
            for selected in candidates:
                data = {"hasNormalizer": True, "profile": value, "catalog": catalog, "capabilities": selected}
                with self.subTest(selected=selected), patch.object(home, "capture", return_value=json.dumps(data)), patch.object(home, "validate_runtime_profile") as runtime:
                    with self.assertRaises(ValueError):
                        home.validate_staged_profile(stage)
                    runtime.assert_not_called()

    def test_target_cannot_return_a_schema_the_helper_does_not_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            value = profile()
            home.write_json(stage / "profile.json", value)
            data = {"hasNormalizer": True, "profile": {**value, "schema": 4}, "catalog": evaluate("project domain")}
            with patch.object(home, "capture", return_value=json.dumps(data)), patch.object(home, "validate_runtime_profile") as runtime:
                with self.assertRaisesRegex(ValueError, "profile schema"):
                    home.validate_staged_profile(stage)
                runtime.assert_not_called()

    def test_target_catalog_support_does_not_override_actual_helper_support(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            home.write_json(stage / "profile.json", profile())
            catalog = {**evaluate("project domain"), "schema": 4}
            data = {"hasNormalizer": True, "profile": profile(), "catalog": catalog,
                    "capabilities": {**home.profile_capabilities(), "catalogSchemas": [4]}}
            for advertised in (True, False):
                selected = copy.deepcopy(data)
                if not advertised:
                    del selected["capabilities"]
                with self.subTest(advertised=advertised), patch.object(home, "capture", return_value=json.dumps(selected)), patch.object(home, "validate_runtime_profile") as runtime:
                    with self.assertRaisesRegex(ValueError, "helper.*catalog schema"):
                        home.validate_staged_profile(stage)
                    runtime.assert_not_called()

    def test_normalizer_cannot_silently_change_supported_schemas(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            home.write_json(stage / "profile.json", profile())
            data = {"hasNormalizer": True, "profile": {**profile(), "schema": 3}, "catalog": evaluate("project domain")}
            with patch.object(home, "capture", return_value=json.dumps(data)), patch.object(home, "validate_runtime_profile") as runtime:
                with self.assertRaisesRegex(ValueError, "changed the profile schema"):
                    home.validate_staged_profile(stage)
                runtime.assert_not_called()

    def test_schema_three_requires_explicit_target_capabilities(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            value = {**profile(), "schema": 3, "capabilities": ["recording"]}
            home.write_json(stage / "profile.json", value)
            data = {"hasNormalizer": True, "profile": value, "catalog": evaluate("project domain")}
            with patch.object(home, "capture", return_value=json.dumps(data)), patch.object(home, "validate_runtime_profile") as runtime:
                with self.assertRaisesRegex(ValueError, "explicit.*capabilities"):
                    home.validate_staged_profile(stage)
                runtime.assert_not_called()

    def test_old_executing_helper_rejects_three_even_when_selected_source_supports_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            home.write_json(stage / "profile.json", {**profile(), "schema": 3})
            old = {**home.profile_capabilities(), "initializeSchemas": [1, 2], "normalizeSchemas": [2], "writeSchema": 2}
            with patch.object(home, "profile_capabilities", return_value=old), patch.object(home, "capture") as capture:
                with self.assertRaisesRegex(ValueError, "helper.*schema"):
                    home.validate_staged_profile(stage)
                capture.assert_not_called()


if __name__ == "__main__":
    unittest.main()

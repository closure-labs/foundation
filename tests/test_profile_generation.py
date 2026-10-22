"""Current profile generation is pure, canonical and independent of a consumer."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_home import ROOT, home
from test_profile_classification import evaluate, ROLE_NAMES


def options(**changes):
    values = dict(foundation="bluefin", hardware=None, roles="", packages="", capabilities="",
                  system=None, form_factor=None, cpu=None, gpus=None, model=None, camera=None, fingerprint=None)
    return argparse.Namespace(**{**values, **changes})


class ProfileGeneration(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.environment = dict(os.environ, FINITE_SKIP_FOUNDATION_CHECK="true",
                                FINITE_HOME_FLAKE_PATH=str(self.base / "consumer"),
                                FINITE_FOUNDATION_SOURCE="/caller/stale/source",
                                FINITE_FOUNDATION_CATALOG="/caller/stale/catalog")
        self.env = patch.dict(os.environ, self.environment)
        self.env.start()
        self.addCleanup(self.env.stop)

    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts/home.py"), "profile", "--foundation", "bluefin", *args],
                              text=True, capture_output=True, env=self.environment)

    def test_minimal_profile_has_no_implicit_roles_or_optional_capabilities(self):
        value = home.generate_profile(options())
        self.assertEqual(value["schema"], 3)
        self.assertEqual(value["roles"], [])
        self.assertEqual(value["packages"], [])
        self.assertEqual(value["capabilities"], [])
        self.assertEqual(value["host"]["formFactor"], "generic")
        self.assertEqual(value["host"]["gpus"], [])
        self.assertEqual(value["hardware"], "generic-x86_64")
        self.assertEqual(Path(value["identity"]["homeDirectory"]).resolve(), Path.home().resolve())

    def test_personal_and_professional_roles_share_canonical_generation(self):
        value = home.generate_profile(options(roles="gaming,creative,media,family,it,developer", packages="uv,jj",
                                              capabilities="recording,office"))
        self.assertEqual(value["roles"], ["developer", "it", "family", "media", "creative", "gaming"])
        self.assertEqual(value["packages"], ["jj", "uv"])
        self.assertEqual(value["capabilities"], ["office", "recording"])
        normalized = evaluate(f'(import {ROOT}/lib/normalize-profile.nix {{catalog = domain;}}) {home.nix_value(value)}')
        self.assertEqual(value, normalized)
        plan = evaluate(f'(import {ROOT}/lib/profile-drafts {{catalog = domain;}}).resolve {home.nix_value(value)}')
        self.assertEqual(plan["classifications"], ["professional", "personal"])
        self.assertIn("obs", plan["applicationIds"])

    def test_dell_adapter_and_explicit_device_overrides(self):
        value = home.generate_profile(options(hardware="dell-xps-9350-intel", camera=False, fingerprint=True))
        self.assertEqual(value["host"]["model"], "dell-xps-9350")
        self.assertEqual(value["host"]["gpus"], ["intel-integrated"])
        self.assertFalse(value["host"]["camera"])
        self.assertTrue(value["host"]["fingerprint"])

    def test_structured_dell_and_mixed_vendor_desktop(self):
        dell = home.generate_profile(options(form_factor="laptop", cpu="intel", gpus="intel-integrated",
                                             model="dell-xps-9350", camera=True, fingerprint=True))
        self.assertEqual(dell["hardware"], "dell-xps-9350-intel")
        desktop = home.generate_profile(options(form_factor="desktop", cpu="intel", gpus="amd-discrete,intel-integrated"))
        self.assertEqual(desktop["host"]["gpus"], ["intel-integrated", "amd-discrete"])
        self.assertEqual(desktop["hardware"], "generic-x86_64")

    def test_invalid_selections_fail_before_stdout(self):
        cases = [("--roles", "family,family"), ("--roles", "unknown"), ("--roles", "family,"),
                 ("--capabilities", "office,office"), ("--capabilities", "unknown"),
                 ("--packages", "uv,uv"), ("--packages", "unknown"),
                 ("--gpus", "amd-discrete,amd-discrete"), ("--gpus", "nvidia-discrete"),
                 ("--system", "aarch64-linux"), ("--form-factor", "phone"),
                 ("--hardware", "dell-xps-9350-intel", "--cpu", "amd"),
                 ("--roles", '${builtins.abort "PROFILE_DATA_EXECUTED"}')]
        for args in cases:
            with self.subTest(args=args):
                result = self.cli(*args, "--format", "json")
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("Invalid Foundation", result.stderr)
                self.assertNotIn("error: PROFILE_DATA_EXECUTED", result.stderr)

    def test_json_and_yaml_outputs_round_trip_to_the_same_object(self):
        args = ["--roles", "media,developer", "--capabilities", "recording", "--camera", "--no-fingerprint"]
        as_json = self.cli(*args, "--format", "json")
        as_yaml = self.cli(*args)
        self.assertEqual(as_json.returncode, 0, as_json.stderr)
        self.assertEqual(as_yaml.returncode, 0, as_yaml.stderr)
        parsed = subprocess.run(["yq", "-o=json", "."], input=as_yaml.stdout, text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(as_json.stdout), json.loads(parsed.stdout))

    def test_running_image_validation_still_applies_after_structural_validation(self):
        running = self.base / "running.json"
        env = {**self.environment, "FINITE_SKIP_FOUNDATION_CHECK": "false", "FINITE_RUNNING_PROFILE_PATH": str(running)}
        for foundation, hardware in (("bluefin-dx", "generic-x86_64"), ("bluefin", "unsupported-image")):
            with self.subTest(foundation=foundation, hardware=hardware):
                home.write_json(running, {"foundation": foundation, "hardware": hardware})
                result = subprocess.run([sys.executable, str(ROOT / "scripts/home.py"), "profile", "--foundation", "bluefin", "--format", "json"],
                                        env=env, text=True, capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("running Finite image", result.stderr)

    def test_generation_uses_bundled_pure_files_without_building_or_touching_a_consumer(self):
        consumer = self.base / "consumer"
        consumer.mkdir()
        (consumer / "sentinel").write_text("unchanged")
        before = home.tree_digest(consumer)
        with patch.object(home, "capture", wraps=home.capture) as capture, patch.object(home, "build") as build, patch.object(home, "commit_stage") as commit, patch.object(home, "provision_brew") as brew:
            home.generate_profile(options(roles="family"))
        command = capture.call_args.args[0]
        self.assertEqual(command[0], "nix-instantiate")
        self.assertEqual(command[1:3], ["--store", "dummy://"])
        self.assertIn(str(ROOT / "lib/generate-profile.nix"), command)
        self.assertNotIn("getFlake", " ".join(command))
        for action in (build, commit, brew):
            action.assert_not_called()
        self.assertEqual(home.tree_digest(consumer), before)
        self.assertFalse((consumer.parent / ".foundation.lock").exists())

    def test_current_catalog_preserves_image_mappings_and_groups_all_ten_roles(self):
        data = evaluate(f'''let domainWithImages = domain // {{
          foundationsByName = builtins.mapAttrs (name: value: value // {{profiles.generic-x86_64.name = if name == "bluefin" then "finite" else "finite-dev";}}) domain.foundationsByName;
        }}; projectCurrent = schema: import {ROOT}/lib/profile-catalog.nix {{domainCatalog = domainWithImages; inherit lib schema; version = "fixture";}};
        in {{current = projectCurrent 3; legacy = projectCurrent 2;}}''')
        current = data["current"]
        self.assertEqual(current["profileSchema"], 3)
        self.assertEqual(current["profileCapabilities"]["writeSchema"], 3)
        self.assertEqual(current["classifications"]["professional"]["roles"], ROLE_NAMES)
        self.assertEqual(current["classifications"]["personal"]["roles"], ["family", "media", "creative", "gaming"])
        self.assertEqual(current["foundations"]["bluefin"]["profiles"], {"generic-x86_64": "finite"})
        self.assertEqual(len(data["legacy"]["roles"]), 6)
        self.assertEqual(data["legacy"]["profileSchema"], 2)
        self.assertIn("recording", current["capabilities"])
        self.assertIn("amd-discrete", current["hosts"]["gpus"])

    def test_default_templates_are_identical_and_normalize_as_schema_three(self):
        value = home.read_json(ROOT / "profile.json")
        self.assertEqual(value, home.read_json(ROOT / "templates/default/profile.json"))
        self.assertEqual(value["schema"], 3)
        normalized = evaluate(f'(import {ROOT}/lib/normalize-profile.nix {{catalog = domain;}}) {home.nix_value(value)}')
        self.assertEqual(normalized, {**value, "hardware": "generic-x86_64"})


if __name__ == "__main__":
    unittest.main()

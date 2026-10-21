"""Host declarations drive composition independently of application roles."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_home import ROOT, home
from test_profile_classification import evaluate
from test_profile_drafts import draft, run_draft


def normalize_host(value, check=True):
    return evaluate(f'(import {ROOT}/lib/hosts.nix).normalize {home.nix_value(value)}', check=check)


class HostProfiles(unittest.TestCase):
    def test_explicit_host_is_authoritative_and_hardware_is_derived(self):
        value = draft(host={"formFactor": "desktop", "cpu": "intel", "gpus": ["amd-discrete"]})
        value.pop("hardware")
        actual = run_draft("normalize", value)
        self.assertEqual(actual["hardware"], "generic-x86_64")
        self.assertEqual(actual["host"]["cpu"], "intel")
        self.assertEqual(actual["host"]["gpus"], ["amd-discrete"])
        self.assertEqual(actual, run_draft("normalize", actual))

    def test_current_hardware_names_have_one_small_adapter(self):
        generic = run_draft("normalize", draft())
        dell = run_draft("normalize", draft(hardware="dell-xps-9350-intel"))
        self.assertEqual(generic["host"]["formFactor"], "generic")
        self.assertEqual(dell["host"]["formFactor"], "laptop")
        self.assertEqual(dell["host"]["cpu"], "intel")
        self.assertEqual(dell["host"]["gpus"], ["intel-integrated"])
        self.assertTrue(dell["host"]["camera"])
        self.assertFalse(dell["host"]["fingerprint"])

    def test_host_dimensions_and_device_types_are_validated(self):
        for value in (None, [], "laptop", {"system": "aarch64-linux"}, {"formFactor": "phone"},
                      {"cpu": "nvidia"}, {"gpus": ["nvidia-discrete"]}, {"gpus": ["amd-discrete", "amd-discrete"]},
                      {"gpus": "intel-integrated"}, {"gpus": [True]}, {"model": "dell"},
                      {"camera": 1}, {"fingerprint": "yes"}, {"gpu": []}):
            with self.subTest(value=value):
                self.assertNotEqual(normalize_host(value, check=False).returncode, 0)

    def test_mixed_gpus_are_canonical_without_implicit_offload(self):
        actual = normalize_host({"formFactor": "desktop", "cpu": "amd",
                                 "gpus": ["amd-discrete", "intel-discrete", "amd-integrated"]})
        self.assertEqual(actual["gpus"], ["intel-discrete", "amd-integrated", "amd-discrete"])
        resolved = run_draft("resolve", draft(host=actual))
        self.assertEqual(resolved["graphics"]["offload"], "explicit-only")
        self.assertFalse(resolved["graphics"]["vulkanDefault"])

    def test_dell_requires_its_observed_form_factor_cpu_and_integrated_gpu(self):
        valid = {"formFactor": "laptop", "cpu": "intel", "gpus": ["intel-integrated"], "model": "dell-xps-9350"}
        self.assertEqual(normalize_host(valid)["model"], "dell-xps-9350")
        for change in ({"formFactor": "desktop"}, {"cpu": "amd"}, {"gpus": []}, {"gpus": ["amd-integrated"]}):
            with self.subTest(change=change):
                self.assertNotEqual(normalize_host({**valid, **change}, check=False).returncode, 0)
        value = draft(hardware="generic-x86_64", host=valid)
        result = run_draft("normalize", value, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("contradicts", result.stderr)

    def test_camera_presence_drives_controls_even_on_generic_desktops(self):
        for camera in (True, False):
            resolved = run_draft("resolve", draft(host={"formFactor": "desktop", "camera": camera}))
            self.assertEqual("camera-controls" in resolved["applicationIds"], camera)
        explicit = run_draft("resolve", draft(host={"camera": False}, capabilities=["camera-controls"]))
        self.assertIn("camera-controls", explicit["applicationIds"])

    def test_role_editing_preserves_declared_host_and_unknown_top_level_fields(self):
        value = draft(host={"formFactor": "laptop", "cpu": "amd", "gpus": ["amd-integrated"], "fingerprint": True}, custom={"keep": True})
        change = {"profile": value, "roles": ["creative"], "capabilities": ["recording"]}
        preview = evaluate(f'(import {ROOT}/lib/profile-changes.nix {{catalog = domain;}}) {home.nix_value(change)}')
        self.assertEqual(preview["source"]["host"], preview["candidate"]["host"])
        self.assertEqual(preview["candidate"]["custom"], {"keep": True})

    def test_workstation_candidate_retains_the_current_application_identities(self):
        candidate = json.loads((ROOT / "examples/workstations/dale-xps-9350.json").read_text())
        original = {key: value for key, value in candidate.items() if key not in ("host", "capabilities")}
        original.update(schema=2, hardware="dell-xps-9350-intel")
        old = run_draft("resolveLegacy", original)
        new = run_draft("resolve", candidate)
        self.assertEqual(old["applicationIds"], new["applicationIds"])
        self.assertEqual(new["profile"]["hardware"], "dell-xps-9350-intel")
        self.assertTrue(new["profile"]["host"]["fingerprint"])
        self.assertEqual(new["classifications"], ["professional"])

    def test_conversion_does_not_repurpose_a_custom_schema_two_host_field(self):
        value = draft(host=normalize_host({}))
        value["schema"] = 2
        for api in ("profile-changes.nix", "profile-drafts"):
            operation = "" if api.endswith(".nix") else ".previewMigration"
            preview = evaluate(f'(import {ROOT}/lib/{api} {{catalog = domain;}}){operation} {home.nix_value({"profile": value, "migrate": True} if not operation else {"profile": value})}')
            self.assertEqual(preview["status"], "blocked")
            self.assertEqual(preview["source"]["host"], value["host"])
            self.assertIsNone(preview["candidate"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "consumer"
            root.mkdir()
            home.write_json(root / "profile.json", value)
            before = home.tree_digest(root)
            with patch.object(home, "editor_target") as target:
                with self.assertRaisesRegex(ValueError, "custom host field"):
                    home.read_editor(root, migrate=True)
                target.assert_not_called()
            self.assertEqual(home.tree_digest(root), before)


if __name__ == "__main__":
    unittest.main()

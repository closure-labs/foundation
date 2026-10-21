"""Executable schema-3 contract, isolated from production readers and writers."""
import json
import unittest

from test_home import ROOT, home
from test_profile_classification import evaluate
from test_profile_validation import profile


def draft(**changes):
    return {**profile(), "schema": 3, "roles": [], "packages": [], **changes}


def expression(value):
    return "(builtins.fromJSON " + home.nix_value(json.dumps(value)) + ")"


def run_draft(operation, value, check=True):
    return evaluate(f'(import {ROOT}/lib/profile-drafts {{catalog = domain;}}).{operation} {expression(value)}', check=check)


class DraftContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = evaluate(f'(import {ROOT}/lib/profile-drafts {{catalog = domain;}}).contract')

    def test_minimal_shape_and_custom_fields_survive_normalization(self):
        value = draft(roles=["creative", "developer"], packages=["uv", "jj"],
                      capabilities=["recording", "office"], custom={"literal": "${untouched}"})
        value["identity"]["custom"] = "retain"
        actual = run_draft("normalize", value)
        self.assertEqual(actual, {**value, "roles": ["developer", "creative"],
                                 "packages": ["jj", "uv"], "capabilities": ["office", "recording"],
                                 "host": evaluate(f'(import {ROOT}/lib/hosts.nix).defaults')})
        self.assertEqual(run_draft("normalize", actual), actual)
        self.assertNotIn("classifications", actual)
        self.assertNotIn("effectiveCapabilities", actual)
        self.assertNotIn("profiles", actual)

    def test_roles_are_independent_and_classifications_are_derived(self):
        for role, metadata in self.contract["roles"].items():
            with self.subTest(role=role):
                actual = run_draft("resolve", draft(roles=[role]))
                self.assertEqual(actual["profile"]["roles"], [role])
                self.assertEqual(actual["classifications"], [metadata["classification"]])
                self.assertTrue(set(metadata["capabilities"]).issubset(actual["effectiveCapabilities"]))
        actual = run_draft("resolve", draft(roles=["support", "media"]))
        self.assertEqual(actual["classifications"], ["professional", "personal"])
        self.assertNotIn("rustup", actual["applicationIds"])
        self.assertNotIn("libreoffice", actual["applicationIds"])

    def test_no_roles_means_shared_defaults_not_every_role(self):
        actual = run_draft("resolve", draft())
        self.assertEqual(actual["classifications"], [])
        self.assertEqual(actual["effectiveCapabilities"], self.contract["commonCapabilities"])
        for application in ("libreoffice", "vlc", "pinta", "devenv", "steam", "gnome-chess"):
            self.assertNotIn(application, actual["applicationIds"])

    def test_shared_capabilities_and_applications_are_deduplicated(self):
        actual = run_draft("resolve", draft(roles=["trainer", "family", "creative"], capabilities=["office", "image-editing"]))
        self.assertEqual(actual["applicationIds"].count("libreoffice"), 1)
        self.assertEqual(actual["applicationIds"].count("pinta"), 1)
        self.assertEqual(actual["declarations"].count("nix:nixpkgs:gradia"), 1)
        self.assertEqual(actual["effectiveCapabilities"].count("image-editing"), 1)

    def test_camera_controls_follow_declared_hardware_and_chromium_is_optional(self):
        generic = run_draft("resolve", draft())
        dell = run_draft("resolve", draft(hardware="dell-xps-9350-intel"))
        explicit = run_draft("resolve", draft(capabilities=["camera-controls", "chromium"]))
        self.assertNotIn("camera-controls", generic["applicationIds"])
        self.assertNotIn("chromium", dell["applicationIds"])
        self.assertIn("camera-controls", dell["applicationIds"])
        self.assertIn("camera-controls", explicit["applicationIds"])
        self.assertIn("chromium", explicit["applicationIds"])

    def test_large_applications_and_launchers_are_optional(self):
        large = {"krita", "kdenlive", "blender", "obs", "steam", "heroic", "lutris", "jellyfin"}
        actual = run_draft("resolve", draft(roles=["family", "media", "creative", "gaming"]))
        self.assertTrue(large.isdisjoint(actual["applicationIds"]))
        self.assertIn("gnome-chess", actual["applicationIds"])
        self.assertIn("gnuchess", actual["applicationIds"])
        explicit = run_draft("resolve", draft(roles=["gaming"], capabilities=["steam"]))
        self.assertIn("steam", explicit["applicationIds"])
        self.assertNotIn("heroic", explicit["applicationIds"])

    def test_graphical_nix_apps_are_wrapped_and_flatpak_exceptions_are_verified(self):
        actual = run_draft("resolve", draft(roles=list(self.contract["roles"]), capabilities=list(self.contract["capabilities"])))
        self.assertEqual(set(actual["wrappedApplicationIds"]),
                         {name for name, app in actual["applications"].items() if app["provider"] == "nix" and app["graphical"]})
        self.assertNotIn("gnuchess", actual["wrappedApplicationIds"])
        self.assertEqual(actual["graphics"]["preferredBackend"], "nixgl-mesa")
        self.assertFalse(actual["graphics"]["globalLibraryExports"])
        verification = evaluate(f'(import {ROOT}/lib/profile-drafts {{catalog = domain;}}).verification')
        for app in actual["applications"].values():
            if app["provider"] == "flatpak":
                evidence = verification["applications"][app["id"]]
                self.assertIs(evidence["verified"], True)
                self.assertTrue(evidence["evidence"].startswith("https://flathub.org/api/v2/appstream/"))
        self.assertEqual(actual["applications"]["spider"]["provider"], "flatpak")

    def test_unknown_or_duplicate_selections_are_rejected(self):
        for change in ({"schema": 2}, {"schema": True}, {"roles": ["unknown"]}, {"roles": ["family", "family"]},
                       {"packages": ["unknown"]}, {"capabilities": ["unknown"]}, {"capabilities": ["office", "office"]},
                       {"capabilities": [["office"]]}, {"capabilities": None}, {"identity": None}, {"hardware": "unknown"}):
            with self.subTest(change=change):
                self.assertNotEqual(run_draft("normalize", draft(**change), check=False).returncode, 0)

    def test_unverified_flatpak_cannot_enter_the_draft_resolution(self):
        result = evaluate(f'''let
          contract = import {ROOT}/lib/profile-drafts/contract.nix {{catalog = domain;}};
          altered = contract // {{applications = contract.applications // {{
            flatseal = contract.applications.flatseal // {{id = "unknown.Unverified";}};
          }};}};
        in (import {ROOT}/lib/profile-drafts {{catalog = domain; applicationContract = altered;}}).resolve {expression(draft())}''', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("verification", result.stderr)

    def test_migration_preview_preserves_fields_and_identifies_provider_changes(self):
        value = {**profile(), "custom": {"preserve": True}}
        actual = run_draft("previewMigration", {"profile": value, "roles": ["developer", "creative"]})
        self.assertEqual(actual["status"], "preview")
        self.assertFalse(actual["activationAllowed"])
        self.assertEqual(actual["candidate"]["custom"], value["custom"])
        self.assertEqual(actual["candidate"]["packages"], ["jj", "uv"])
        self.assertEqual(actual["candidate"]["hardware"], value["hardware"])
        changes = {row["application"]: row for row in actual["changes"]["providerChanges"]}
        self.assertEqual(changes["pinta"]["before"], "flatpak:flathub:com.github.PintaProject.Pinta")
        self.assertEqual(changes["pinta"]["after"], "nix:nixpkgs:pinta")
        self.assertFalse(actual["flatpak"]["uninstallUnmanaged"])
        self.assertFalse(actual["flatpak"]["deleteApplicationData"])
        self.assertFalse(actual["flatpak"]["migrateApplicationDataAutomatically"])

    def test_custom_capabilities_collision_blocks_instead_of_overwriting(self):
        for custom in ([], ["office"], {"private": True}, None):
            value = {**profile(), "capabilities": custom}
            with self.subTest(custom=custom):
                actual = run_draft("previewMigration", {"profile": value})
                self.assertEqual(actual["status"], "blocked")
                self.assertEqual(actual["source"]["capabilities"], custom)
                self.assertIsNone(actual["candidate"])
                self.assertFalse(actual["activationAllowed"])

    def test_production_reader_catalog_and_default_writer_use_three(self):
        actual = evaluate(f'''{{
          catalog = import {ROOT}/lib/profile-catalog.nix {{ domainCatalog = domain; inherit lib; version = "fixture"; }};
          canRead = builtins.tryEval ((import {ROOT}/lib/normalize-profile.nix {{catalog = domain;}}) {expression(draft())});
        }}''')
        self.assertTrue(actual["canRead"]["success"])
        self.assertEqual(len(actual["catalog"]["roles"]), 10)
        self.assertIn("family", actual["catalog"]["roles"])
        self.assertEqual(actual["catalog"]["profileCapabilities"]["normalizeSchemas"], [2, 3])
        self.assertEqual(actual["catalog"]["profileCapabilities"]["writeSchema"], 3)

    def test_legacy_inventory_covers_actual_module_declarations(self):
        actual = evaluate(f'import {ROOT}/tests/profile-inventory.nix')
        applications = self.contract["legacyApplications"]
        expected_common = sorted(applications[name]["declaration"] for name in self.contract["legacy"]["commonApplications"])
        self.assertEqual(actual["common"], expected_common)
        for name, application_ids in self.contract["legacy"]["roleApplications"].items():
            with self.subTest(role=name):
                self.assertEqual(actual["roles"][name], sorted(applications[app]["declaration"] for app in application_ids))
        used = set(self.contract["legacy"]["commonApplications"])
        for values in self.contract["legacy"]["roleApplications"].values():
            used.update(values)
        self.assertEqual(len(used), 44)
        owned = {app for capability in self.contract["capabilities"].values() for app in capability["applications"]}
        self.assertTrue(used.issubset(owned))

    def test_legacy_resolver_remains_strictly_schema_two(self):
        self.assertNotEqual(run_draft("resolveLegacy", draft(), check=False).returncode, 0)

    def test_production_three_normalizer_preserves_capabilities_and_extensions(self):
        value = draft(roles=["family", "developer"], capabilities=["recording", "office"], custom={"keep": True})
        actual = evaluate(f'(import {ROOT}/lib/normalize-profile.nix {{catalog = domain;}}) {expression(value)}')
        self.assertEqual(actual, run_draft("normalize", value))


if __name__ == "__main__":
    unittest.main()

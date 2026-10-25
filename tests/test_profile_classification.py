"""Offline catalog contracts and selector round trips with a fake desktop."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ROLE_NAMES = ["developer", "sales", "trainer", "support", "executive", "it"]
# The projection only needs these two standard library operations. Keeping
# them local makes the fixture independent of a Nix daemon or fetched inputs;
# the full Home Manager evaluations also exercise the real nixpkgs library.
NIX_SETUP = f'''
let
  lib = {{
    inherit (builtins) mapAttrs;
    genAttrs = names: f: builtins.listToAttrs (map (name: {{ inherit name; value = f name; }}) names);
  }};
  domain = import {ROOT}/lib/catalog.nix;
  project = domainCatalog: import {ROOT}/lib/home-catalog.nix {{
    inherit domainCatalog lib;
    version = "fixture";
  }};
in
'''


def evaluate(expression, check=True):
    result = subprocess.run(
        ["nix-instantiate", "--eval", "--strict", "--json", "--expr", NIX_SETUP + expression],
        text=True, capture_output=True, check=check,
    )
    return json.loads(result.stdout) if check else result


class CatalogTests(unittest.TestCase):
    def test_all_existing_work_roles_are_professional(self):
        data = evaluate("{ inherit (domain) classifications classificationNames; catalog = project domain; }")
        self.assertEqual(data["classificationNames"], ["professional", "personal"])
        self.assertEqual([(x["label"], x["order"]) for x in data["classifications"]],
                         [("Professional", 10), ("Personal", 20)])
        home = data["catalog"]
        self.assertEqual(home["classifications"]["professional"]["roles"], ROLE_NAMES)
        self.assertEqual(home["classifications"]["personal"]["roles"], [])
        self.assertEqual(home["schema"], 3)
        for role in ROLE_NAMES:
            self.assertEqual(home["roles"][role]["classification"], "professional")

    def test_old_custom_catalog_stays_unclassified(self):
        home = evaluate('''project (domain // {
          classifications = [];
          rolesByName = builtins.mapAttrs (_: role: builtins.removeAttrs role ["classification"]) domain.rolesByName;
        })''')
        self.assertEqual(home["classifications"], {})
        self.assertTrue(all(x["classification"] is None for x in home["roles"].values()))
        absent = evaluate('''project ((builtins.removeAttrs domain ["classifications"]) // {
          rolesByName = builtins.mapAttrs (_: role: builtins.removeAttrs role ["classification"]) domain.rolesByName;
        })''')
        self.assertEqual(absent, home)

    def test_membership_is_derived_from_role_metadata(self):
        home = evaluate('''project (domain // {
          rolesByName = domain.rolesByName // {
            support = domain.rolesByName.support // { classification = "personal"; };
          };
        })''')
        self.assertEqual(home["classifications"]["personal"]["roles"], ["support"])
        self.assertEqual(home["classifications"]["professional"]["roles"],
                         [x for x in ROLE_NAMES if x != "support"])

    def test_unknown_classification_is_rejected(self):
        result = evaluate('''project (domain // {
          rolesByName = domain.rolesByName // {
            developer = domain.rolesByName.developer // { classification = "missing"; };
          };
        })''', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("classification", result.stderr)
        self.assertIn("missing", result.stderr)

    def test_finite_image_mapping_and_existing_flags_are_preserved(self):
        data = evaluate('''{
          compatible = domain.homeCompatibleRoleNames;
          catalog = project (domain // {
            foundationsByName = builtins.mapAttrs (name: foundation: foundation // {
              profiles.generic-x86_64.name = if name == "bluefin" then "finite" else "finite-dev";
            }) domain.foundationsByName;
          });
        }''')
        self.assertEqual(data["compatible"], ["sales", "trainer", "support"])
        self.assertEqual(data["catalog"]["foundations"]["bluefin"]["profiles"],
                         {"generic-x86_64": "finite"})
        self.assertEqual(data["catalog"]["foundations"]["bluefin-dx"]["profiles"],
                         {"generic-x86_64": "finite-dev"})
        self.assertEqual(data["catalog"]["classifications"]["professional"]["roles"], ROLE_NAMES)


class SelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = evaluate("project domain")

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.profile = self.root / "profile.json"
        self.profile.write_text(json.dumps({
            "schema": 2, "roles": ["developer", "sales"], "packages": ["uv"],
        }))
        self.catalog_path = self.root / "catalog.json"
        self.catalog_path.write_text(json.dumps(self.catalog))
        self.log = self.root / "events.jsonl"
        for name in ("zenity", "finite-home-apply"):
            mock = self.bin / name
            mock.write_text(f"#!{sys.executable}\n" + '''import json, os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
if name == "finite-home-apply" and "--editor-context" in sys.argv:
    value = json.loads(Path(os.environ["FINITE_HOME_PROFILE_PATH"]).read_text())
    catalog = json.loads(Path(os.environ["FINITE_FOUNDATION_CATALOG"]).read_text())
    print(json.dumps({"schema": 1, "profile": value, "catalog": catalog, "canMigrate": True}))
    sys.exit(0)
with Path(os.environ["SELECTOR_LOG"]).open("a") as stream:
    stream.write(json.dumps([name, *sys.argv[1:]]) + "\\n")
if name == "zenity":
    stage = ("packages" if "--title=Configure Finite packages" in sys.argv else
             "capabilities" if "--title=Additional capabilities" in sys.argv else
             "review" if "--text-info" in sys.argv else "roles")
    if os.environ.get("SELECTOR_CANCEL") == stage:
        sys.exit(1)
    if stage != "review":
        print(os.environ.get("SELECTOR_PACKAGES", "jj,uv") if stage == "packages" else
              os.environ.get("SELECTOR_CAPABILITIES", "recording") if stage == "capabilities" else
              os.environ.get("SELECTOR_ROLES", "developer,support"))
elif "--preview" in sys.argv:
    print(json.dumps({"schema": 1, "preview": {"status": "preview", "activationAllowed": False},
                      "summary": "Review app and provider changes. Existing Flatpaks and data are kept.", "approvalToken": "a" * 64}))
else:
    sys.exit(int(os.environ.get("SELECTOR_APPLY_STATUS", "0")))
''')
            mock.chmod(0o755)
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ["PATH"],
                        FINITE_HOME_PROFILE_PATH=str(self.profile),
                        FINITE_FOUNDATION_CATALOG=str(self.catalog_path), SELECTOR_LOG=str(self.log))

    def run_selector(self, *arguments, **overrides):
        before = self.profile.read_bytes()
        result = subprocess.run(["bash", str(ROOT / "modules/_legacy/finite-configure"), *arguments],
                                env={**self.env, **overrides}, text=True, capture_output=True)
        self.assertEqual(self.profile.read_bytes(), before)
        events = [json.loads(x) for x in self.log.read_text().splitlines()] if self.log.exists() else []
        return result, events

    def test_accept_preserves_ids_checked_state_and_single_apply(self):
        result, events = self.run_selector()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([x[0] for x in events], ["zenity", "zenity", "finite-home-apply"])
        roles = events[0]
        self.assertIn("--column=Classification", roles)
        self.assertIn("--hide-column=4", roles)
        self.assertIn("--print-column=4", roles)
        start = roles.index("TRUE")
        self.assertEqual(roles[start:], [
            "TRUE", "Professional", "Developer", "developer",
            "TRUE", "Professional", "Sales", "sales",
            "FALSE", "Professional", "Trainer", "trainer",
            "FALSE", "Professional", "Support", "support",
            "FALSE", "Professional", "Executive", "executive",
            "FALSE", "Professional", "IT", "it",
        ])
        self.assertNotIn("Personal", roles)
        packages = events[1]
        start = packages.index("FALSE")
        rows = packages[start:]
        self.assertEqual(rows[3::4], ["hack-font", "herdr", "jj", "opencode", "uv"])
        self.assertEqual(rows[0::4], ["FALSE", "FALSE", "FALSE", "FALSE", "TRUE"])
        self.assertEqual(events[2], ["finite-home-apply", "--roles", "developer,support", "--packages", "jj,uv"])

    def test_cancel_either_dialog_never_applies(self):
        for stage, count in (("roles", 1), ("packages", 2)):
            with self.subTest(stage=stage):
                self.log.unlink(missing_ok=True)
                result, events = self.run_selector(SELECTOR_CANCEL=stage)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual([x[0] for x in events], ["zenity"] * count)

    def test_empty_selections_are_passed_as_empty_arguments(self):
        result, events = self.run_selector(SELECTOR_ROLES="", SELECTOR_PACKAGES="")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(events[-1], ["finite-home-apply", "--roles", "", "--packages", ""])

    def test_apply_failure_propagates(self):
        result, events = self.run_selector(SELECTOR_APPLY_STATUS="7")
        self.assertEqual(result.returncode, 7)
        self.assertEqual(sum(x[0] == "finite-home-apply" for x in events), 1)

    def test_rows_come_from_catalog_including_unclassified_custom_roles(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["roles"] = {"support": {**catalog["roles"]["support"], "label": "Custom Support", "classification": None}}
        catalog["packages"] = {"uv": catalog["packages"]["uv"]}
        self.catalog_path.write_text(json.dumps(catalog))
        result, events = self.run_selector()
        self.assertEqual(result.returncode, 0, result.stderr)
        start = events[0].index("FALSE")
        self.assertEqual(events[0][start:], ["FALSE", "", "Custom Support", "support"])
        start = events[1].index("TRUE")
        self.assertEqual(events[1][start:], ["TRUE", "uv", "Python package and project manager", "uv"])

    def test_missing_or_invalid_catalog_fails_before_dialogs(self):
        malformed_role = copy.deepcopy(self.catalog)
        malformed_role["roles"]["developer"]["label"] = []
        malformed_package = copy.deepcopy(self.catalog)
        malformed_package["packages"]["uv"]["description"] = 42
        malformed_category = copy.deepcopy(self.catalog)
        malformed_category["classifications"]["professional"]["label"] = []
        for contents in (None, "not JSON", "{}", json.dumps(malformed_role),
                         json.dumps(malformed_package), json.dumps(malformed_category)):
            with self.subTest(contents=contents):
                if contents is None:
                    self.catalog_path.unlink(missing_ok=True)
                else:
                    self.catalog_path.write_text(contents)
                result, events = self.run_selector()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(events, [])
                self.assertIn("catalog", result.stderr.lower())

    def test_schema_three_requires_a_capability_catalog_before_any_dialog(self):
        value = {"schema": 3, "roles": ["family", "developer"], "packages": ["jj"],
                 "capabilities": ["recording"], "custom": {"retain": True}}
        self.profile.write_text(json.dumps(value))
        result, events = self.run_selector()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(events, [])
        self.assertIn("capability catalog", result.stderr)

    def schema_three(self, source_schema=3):
        contract = f'(import {ROOT}/lib/profile-drafts {{catalog = domain;}}).contract'
        catalog = evaluate(f'''let c = {contract}; in (project (domain // {{
          rolesByName = c.roles; roleNames = builtins.attrNames c.roles;
        }})) // {{ profileSchema = 3; capabilities = c.capabilities; }}''')
        self.catalog_path.write_text(json.dumps(catalog))
        self.profile.write_text(json.dumps({"schema": source_schema, "roles": ["family"] if source_schema == 3 else ["developer"],
                                           "packages": ["uv"], **({"capabilities": ["recording"]} if source_schema == 3 else {})}))

    def test_schema_three_checks_only_explicit_capabilities_and_reviews_exact_selections(self):
        self.schema_three()
        result, events = self.run_selector(SELECTOR_ROLES="family,creative", SELECTOR_CAPABILITIES="recording,notes")
        self.assertEqual(result.returncode, 0, result.stderr)
        dialog = events[2]
        rows = dialog[dialog.index("FALSE"):]
        checked = dict(zip(rows[3::4], rows[0::4]))
        self.assertEqual(checked["office"], "FALSE")
        self.assertEqual(checked["essentials"], "FALSE")
        self.assertEqual(checked["recording"], "TRUE")
        preview, review, applied = events[3:]
        expected = ["finite-home-apply", "--roles", "family,creative", "--packages", "jj,uv", "--capabilities", "recording,notes"]
        self.assertEqual(preview, expected + ["--preview"])
        self.assertIn("--text-info", review)
        self.assertEqual(applied, expected + ["--approve-preview", "a" * 64])
        self.assertIn("Personal", events[0])

    def test_cancellation_at_every_schema_three_dialog_never_applies(self):
        self.schema_three()
        for stage in ("roles", "packages", "capabilities", "review"):
            self.log.unlink(missing_ok=True)
            result, events = self.run_selector(SELECTOR_CANCEL=stage)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(any(event[0] == "finite-home-apply" and "--preview" not in event for event in events))

    def test_conversion_is_only_requested_explicitly(self):
        self.schema_three(source_schema=2)
        result, events = self.run_selector("--migrate-profile", SELECTOR_ROLES="family")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [event for event in events if event[0] == "finite-home-apply"]
        self.assertEqual(len(calls), 2)
        self.assertTrue(all("--migrate-profile" in event for event in calls))


if __name__ == "__main__":
    unittest.main()

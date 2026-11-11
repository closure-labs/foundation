"""Pure discovery and graph extension contracts; no Nixpkgs or flake fetches."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]


def evaluate(expression, check=True):
    return subprocess.run(["nix-instantiate", "--store", "dummy://", "--eval", "--strict", "--json", "--expr", expression],
                          text=True, capture_output=True, check=check)


class Features(unittest.TestCase):
    def test_public_compatibility_aliases_and_generic_imports(self):
        # Mock canonical aliases, keeping this contract independent of locked inputs.
        expression = r'''let
          loader = import ROOT/modules/flake/features/_loader.nix {};
          den.aspects.foundation = builtins.mapAttrs (id: _: id) loader.features;
          lib.genAttrs = names: f: builtins.listToAttrs (map (name: { inherit name; value = f name; }) names);
          exported = (import ROOT/modules/home/construction/_aspects.nix { inherit den lib; }).den.aspects.features;
          generic = exported.hardware.generic-x86_64.homeManager.imports;
        in {
          base = exported.base;
          host = exported.host;
          composition = exported.profile-composition;
          devops = exported.capabilities.devops;
          roles = exported.roles;
          machines = exported.machines;
          cpu = exported.hardware.cpu;
          gpu = exported.hardware.gpu;
          models = exported.hardware.models;
          dell = exported.hardware.dell-xps-9350-intel;
          genericPathsExist = map builtins.pathExists generic;
          genericHardware = (import (builtins.elemAt generic 1) {}).home.sessionVariables.FINITE_HARDWARE;
        }'''.replace("ROOT", str(ROOT))
        result = json.loads(evaluate(expression).stdout)
        self.assertEqual(result["base"], "home/base")
        self.assertEqual(result["host"], "hosts/identity")
        self.assertEqual(result["composition"], "profiles/composition")
        self.assertEqual(result["devops"], "capabilities/devops")
        expected_names = {
            "roles": ["developer", "sales", "trainer", "support", "executive", "it", "family", "media", "creative", "gaming"],
            "machines": ["generic", "laptop", "desktop"],
            "cpu": ["generic", "intel", "amd"],
            "gpu": ["intel-integrated", "intel-discrete", "amd-integrated", "amd-discrete"],
            "models": ["generic", "dell-xps-9350"],
        }
        for group, prefix in (("roles", "roles"), ("machines", "hosts/machines"),
                              ("cpu", "hosts/cpu"), ("gpu", "hosts/gpu"), ("models", "hosts/models")):
            self.assertEqual(set(result[group]), set(expected_names[group]))
            self.assertEqual(result[group], {name: f"{prefix}/{name}" for name in result[group]})
        self.assertEqual(result["dell"], "hosts/models/dell-xps-9350")
        self.assertEqual(result["genericPathsExist"], [True, True])
        self.assertEqual(result["genericHardware"], "generic-x86_64")

    def test_discovery_extension_is_pure_and_private_files_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("modules", "lib"):
                shutil.copytree(ROOT/name, root/name)
            shutil.copy(ROOT/"profile.json",root/"profile.json")
            shutil.copy(ROOT/"VERSION",root/"VERSION")
            feature = root/"modules/apps/new-feature"
            feature.mkdir()
            (feature/"_feature.nix").write_text('{ id = "apps/new-feature"; metadata = {}; dependencies = ["apps/firefox"]; schemaDependencies = {}; configuration = _: throw "must stay lazy"; }')
            (feature/"default.nix").write_text('{...}: { foundation.features."apps/new-feature" = import ./_feature.nix; }')
            (feature/"_private.nix").write_text('throw "never auto-import"')
            expr = f'(import {root}/modules/flake/features/_loader.nix {{}})'
            ids = json.loads(evaluate(f'builtins.attrNames {expr}.features').stdout)
            self.assertIn("apps/new-feature",ids)
            selected = json.loads(evaluate(f'{expr}.closure 3 ["home/base"]').stdout)
            self.assertNotIn("apps/new-feature",selected)
            graph = json.loads(evaluate(f'import {root}/modules/ci/_graph.nix').stdout)
            self.assertIn("apps/new-feature",graph["features"])
            self.assertIn("modules/apps/new-feature/_private.nix",graph["features"]["apps/new-feature"]["files"])
            for body in (
                '{ id = "apps/firefox"; metadata = {}; dependencies = []; schemaDependencies = {}; }',
                '{ id = "apps/new-feature"; metadata = {}; dependencies = ["missing"]; schemaDependencies = {}; }',
                '{ id = "apps/new-feature"; metadata = {}; dependencies = ["apps/new-feature"]; schemaDependencies = {}; }',
            ):
                (feature/"_feature.nix").write_text(body)
                self.assertNotEqual(evaluate(f'builtins.attrNames {expr}.features',check=False).returncode,0)


if __name__ == "__main__": unittest.main()

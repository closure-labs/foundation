"""The public constructor must preserve owned inputs without forcing personal ones."""
import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ConstructorInputsTests(unittest.TestCase):
    def evaluate(self, arguments, result="builtins.attrNames args.specialArgs.inputs"):
        # Exercise the real API with a module-evaluator test double. No flake
        # fetching, package construction, store writes or host activation.
        expression = '''let
          inputs = {
            self = { marker = "foundation"; };
            nixpkgs = {
              marker = "owned-stable";
              lib.evalModules = args: {
                config.flake.homeConfigurations.${args.specialArgs.foundationProfile.identity.username} = RESULT;
              };
            };
            nixpkgs-weekly = { marker = "owned-weekly"; };
            nixpkgs-unstable = { marker = "owned-unstable"; };
            home-manager = {};
            den = { flakeModule = {}; flakeOutputs.homeConfigurations = {}; };
            future-owned-input = {};
          };
          api = import API { inherit inputs; };
        in api.mkHomeConfiguration {
          profile = builtins.fromJSON (builtins.readFile PROFILE);
          ARGUMENTS
        }'''.replace("RESULT", result).replace(
            "API", str(ROOT / "modules/flake/exports/_api.nix")).replace(
            "PROFILE", str(ROOT / "profile.json")).replace("ARGUMENTS", arguments)
        return subprocess.run([
            "nix-instantiate", "--store", "dummy://", "--eval", "--strict", "--json", "--expr", expression,
        ], text=True, capture_output=True)

    def test_empty_default_and_unrelated_inputs_preserve_owned_values(self):
        selected = '''{
          stable = args.specialArgs.inputs.nixpkgs.marker;
          weekly = args.specialArgs.inputs.nixpkgs-weekly.marker;
          unstable = args.specialArgs.inputs.nixpkgs-unstable.marker;
        }'''
        for arguments in ("", "extraInputs = {};", 'extraInputs.personal-nixpkgs = throw "unused personal input forced";'):
            with self.subTest(arguments=arguments):
                result = self.evaluate(arguments, selected)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), {
                    "stable": "owned-stable", "weekly": "owned-weekly", "unstable": "owned-unstable",
                })
        result = self.evaluate('extraInputs.personal-nixpkgs.marker = "personal";',
                               "args.specialArgs.inputs.personal-nixpkgs.marker")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), "personal")

    def test_every_owned_name_is_rejected_before_module_evaluation(self):
        for name in ("self", "nixpkgs", "nixpkgs-weekly", "nixpkgs-unstable", "home-manager", "den", "future-owned-input"):
            with self.subTest(name=name):
                result = self.evaluate(f'extraInputs.{name} = throw "replacement forced";',
                                       'throw "home evaluation reached"')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("cannot replace owned inputs: " + name, result.stderr)
                self.assertIn("Rename personal inputs", result.stderr)
                self.assertNotIn("replacement forced", result.stderr.split("error:")[-1])
                self.assertNotIn("home evaluation reached", result.stderr.split("error:")[-1])
        result = self.evaluate('extraInputs = { self = {}; nixpkgs = {}; };')
        self.assertIn("cannot replace owned inputs: nixpkgs, self", result.stderr)

    def test_invalid_extra_input_types_fail_with_argument_guidance(self):
        for value in ('[]', 'null', '"nixpkgs"', '42', 'true'):
            with self.subTest(value=value):
                result = self.evaluate(f"extraInputs = {value};", 'throw "home evaluation reached"')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("mkHomeConfiguration.extraInputs must be an attribute set", result.stderr)


if __name__ == "__main__":
    unittest.main()

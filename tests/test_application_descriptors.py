"""The small pure descriptor helper preserves metadata and dependency ordering."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


def evaluate(expression):
    return json.loads(subprocess.check_output([
        "nix-instantiate", "--store", "dummy://", "--eval", "--strict", "--json", "--expr", expression,
    ], text=True))


class ApplicationDescriptorTests(unittest.TestCase):
    def test_migrated_descriptors_are_exactly_equivalent(self):
        for name, attribute in (("bitwarden", "bitwarden-desktop"), ("element", "element-desktop"),
                                ("nextcloud", "nextcloud-client"), ("libreoffice", "libreoffice")):
            with self.subTest(name=name):
                descriptor = evaluate(f'builtins.removeAttrs (import {ROOT}/modules/apps/{name}/_feature.nix) ["configuration"]')
                self.assertEqual(descriptor, {
                    "id": f"apps/{name}",
                    "metadata": {"application": {"attribute": attribute, "declaration": f"nix:nixpkgs-weekly:{attribute}",
                                "graphical": True, "input": "nixpkgs-weekly", "provider": "nix"}},
                    "dependencies": ["providers/nixpkgs-weekly", "providers/graphics"],
                    "schemaDependencies": {},
                })
                function = evaluate(f'builtins.isFunction ((import {ROOT}/modules/apps/{name}/_feature.nix).configuration 3)')
                self.assertTrue(function)

    def test_non_graphical_helper_does_not_add_graphics_dependency(self):
        result = evaluate(f'''builtins.removeAttrs (import {ROOT}/modules/profiles/composition/_nix-application-feature.nix {{
            name = "fixture"; input = "nixpkgs"; attribute = "hello";
        }}) ["configuration"]''')
        self.assertEqual(result["dependencies"], ["providers/nixpkgs"])
        self.assertFalse(result["metadata"]["application"]["graphical"])

    def test_custom_recipes_remain_explicit(self):
        recipes = evaluate(f'''builtins.mapAttrs (_: feature: feature.metadata.application.recipe) {{
            firefox = import {ROOT}/modules/apps/firefox/_feature.nix;
            ghostty = import {ROOT}/modules/apps/ghostty/_feature.nix;
        }}''')
        self.assertEqual(recipes, {"firefox": "configured-firefox", "ghostty": "finite-ghostty"})


if __name__ == "__main__":
    unittest.main()

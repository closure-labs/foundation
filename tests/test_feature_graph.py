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

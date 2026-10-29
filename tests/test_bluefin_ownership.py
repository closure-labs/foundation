"""The Bluefin aspect configures stock tools without installing duplicate copies."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BluefinOwnershipTests(unittest.TestCase):
    def test_aspect_adds_no_cli_packages_and_keeps_integration(self):
        expression = '''let
          module = import ROOT/modules/hosts/os/bluefin/_home.nix {
            inputs = {};
            foundationPackageSets.nixpkgs-unstable.bbrew = "bbrew";
            pkgs = {
              bbrew = "bbrew"; ugrep = "ugrep"; uutils-coreutils = "uutils-coreutils";
              python3 = "python3";
              runCommand = _: _: _: "/preparation-source";
              writeShellApplication = _: "/preparation";
            };
            lib.mkOrder = order: content: { inherit order content; };
          };
        in {
          packages = module.home.packages or [];
          shell = module.programs.zsh.initContent;
          preparation = module.home.extraBuilderCommands;
        }'''.replace("ROOT", str(ROOT))
        actual = json.loads(subprocess.check_output([
            "nix-instantiate", "--store", "dummy://", "--eval", "--strict", "--json", "--expr", expression,
        ], text=True))
        self.assertEqual(actual["packages"], [])
        self.assertEqual(actual["shell"]["order"], 910)
        self.assertIn("/home/linuxbrew/.linuxbrew/bin/fzf --zsh", actual["shell"]["content"])
        self.assertIn('"$out/foundation-prepare"', actual["preparation"])


if __name__ == "__main__":
    unittest.main()

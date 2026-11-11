"""Verify public import-tree discovery and private-file exclusion with locked inputs."""
import json
from pathlib import Path
import subprocess
import tempfile
from test_home import ROOT


def evaluate(body):
    expression = 'let f = builtins.getFlake ' + json.dumps("path:" + str(ROOT)) + '; in ' + body
    return json.loads(subprocess.check_output(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expression],text=True))


def main():
    ids = evaluate('{ public = f.lib.discoveredFeatures; pure = builtins.attrNames (import (f.outPath + "/modules/flake/features/_loader.nix") {}).features; }')
    assert ids["public"] == ids["pure"], ids
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root/"default.nix").write_text('{ discovery = true; }')
        (root/"_feature.nix").write_text('throw "private descriptor must not be imported"')
        (root/"_assets").mkdir()
        (root/"_assets/invalid.nix").write_text('not valid Nix syntax !')
        body = '(f.inputs.nixpkgs.lib.evalModules { modules = [(f.inputs.import-tree ' + str(root) + ') ({lib,...}: { options.discovery = lib.mkOption {type=lib.types.bool;}; })]; }).config.discovery'
        assert evaluate(body) is True
    print("Public discovery matches pure discovery; import-tree excludes private descriptors and assets",flush=True)


if __name__ == "__main__": main()

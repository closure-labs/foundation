"""Validate the typed pre-construction policy on all locked Nixpkgs channels."""
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CHANNELS = ("nixpkgs", "nixpkgs-weekly", "nixpkgs-unstable")
PREFIX = 'let f = builtins.getFlake ' + json.dumps("path:" + str(ROOT)) + '; '


def evaluate(body, check=True, environment=None):
    environment = {key: value for key, value in os.environ.items() if key != "NIXPKGS_ALLOW_UNFREE"} | (environment or {})
    return subprocess.run(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", PREFIX + body],
                          check=check, text=True, capture_output=True, env=environment)


def fixture(policy, channel, name="foundation-policy-fixture"):
    return '''sets = import (f.outPath + "/modules/providers/nixpkgs/_package-sets.nix") {
      inputs = f.inputs; system = "x86_64-linux"; packagePolicy = POLICY;
    }; pkgs = sets.CHANNEL;
    in (pkgs.runCommand "NAME" { meta.license = pkgs.lib.licenses.unfree; } "touch $out").drvPath
    '''.replace("POLICY", policy).replace("CHANNEL", channel).replace("NAME", name)


def main():
    defaults = json.loads(evaluate('''sets = import (f.outPath + "/modules/providers/nixpkgs/_package-sets.nix") {
      inputs = f.inputs; system = "x86_64-linux";
    }; in builtins.mapAttrs (_: pkgs: pkgs.config.allowUnfree) sets''').stdout)
    assert defaults == {channel: True for channel in CHANNELS}, defaults
    for channel in CHANNELS:
        allow = evaluate(fixture("{}", channel)).stdout
        explicit = evaluate(fixture('{ unfree = "allow"; }', channel)).stdout
        allowlist = evaluate(fixture('{ unfree = "allowlist"; allowedUnfreePackages = ["foundation-policy-fixture"]; }', channel)).stdout
        assert allow == explicit == allowlist, channel
        for policy in ('{ unfree = "deny"; }', '{ unfree = "allowlist"; }',
                       '{ unfree = "allowlist"; allowedUnfreePackages = ["different-package"]; }'):
            rejected = evaluate(fixture(policy, channel), check=False)
            assert rejected.returncode != 0, (channel, policy)
            assert "Foundation packagePolicy rejected unfree package 'foundation-policy-fixture'" in rejected.stderr, rejected.stderr
    for policy in ('{ unfree = "deny"; }', '{ unfree = "allowlist"; allowedUnfreePackages = ["foundation-policy-fixture"]; }'):
        for channel in CHANNELS:
            result = evaluate(fixture(policy, channel), check=False, environment={"NIXPKGS_ALLOW_UNFREE": "1"})
            assert result.returncode != 0 and "NIXPKGS_ALLOW_UNFREE to be unset" in result.stderr, result.stderr
    homes = []
    for policy in ("{}", '{ unfree = "allow"; }'):
        homes.append(json.loads(evaluate('''profile = builtins.fromJSON (builtins.readFile (f.outPath + "/profile.json"));
          home = f.lib.mkHomeConfiguration { inherit profile; packagePolicy = POLICY; };
          in {
            activation = home.activationPackage.drvPath;
            services = builtins.attrNames home.config.systemd.user.services;
            stateVersion = home.config.home.stateVersion;
          }'''.replace("POLICY", policy)).stdout))
    assert homes[0] == homes[1], homes
    assert homes[0]["stateVersion"] == "26.05", homes
    for value in ('{ unfree = "maybe"; }', '{ unfree = false; }',
                  '{ allowedUnfreePackages = [42]; }', '{ unknown = true; }',
                  '{ unfree = "deny"; allowedUnfreePackages = ["steam"]; }',
                  '{ unfree = "allowlist"; allowedUnfreePackages = [""]; }'):
        result = evaluate('policy = import (f.outPath + "/modules/providers/nixpkgs/_policy.nix") { lib = f.inputs.nixpkgs.lib; }; in policy ' + value, check=False)
        assert result.returncode != 0, value
        assert "packagePolicy" in result.stderr, result.stderr
    print("Package policy: default/explicit allow parity, deny and allowlist across all channels; invalid policies rejected", flush=True)


if __name__ == "__main__":
    main()

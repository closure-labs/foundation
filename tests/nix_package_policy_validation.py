"""Validate the typed pre-construction policy on all locked Nixpkgs channels."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

from test_home import home, INFO

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


def validate_generated_customization():
    with tempfile.TemporaryDirectory(prefix="foundation-policy-template-") as temporary:
        consumer = Path(temporary) / "consumer"
        home.make_template(ROOT, INFO, consumer)
        customization = consumer / "customize.nix"
        text = customization.read_text()
        assert text.count("# example") == 1, "Expected the public weekly package example"
        customization.write_text(text.replace("# example", '''(runCommand "foundation-policy-fixture" {
          meta.license = lib.licenses.unfree;
        } "touch $out")'''))

        def generated(policy, check=True):
            return evaluate('''sets = import (f.outPath + "/modules/providers/nixpkgs/_package-sets.nix") {
                inputs = f.inputs; system = "x86_64-linux"; packagePolicy = POLICY;
              };
              custom = import (builtins.toPath CUSTOMIZATION) {
                inputs = f.inputs; pkgs = sets.nixpkgs; foundationPackageSets = sets;
              };
              in map (package: package.drvPath) custom.home.packages'''
                .replace("POLICY", policy).replace("CUSTOMIZATION", home.nix_value(str(customization))), check=check)

        default = generated("{}", check=False)
        assert default.returncode == 0, default.stderr
        allowed = default.stdout
        assert len(json.loads(allowed)) == 1, allowed
        assert allowed == generated('{ unfree = "allow"; }').stdout
        assert allowed == generated('{ unfree = "allowlist"; allowedUnfreePackages = ["foundation-policy-fixture"]; }').stdout
        for policy in ('{ unfree = "deny"; }', '{ unfree = "allowlist"; }'):
            rejected = generated(policy, check=False)
            assert rejected.returncode != 0 and "Foundation packagePolicy rejected unfree package" in rejected.stderr, rejected.stderr


def main():
    validate_generated_customization()
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
    print("Package policy: default/explicit allow parity, deny and allowlist across all channels and generated customization; invalid policies rejected", flush=True)


if __name__ == "__main__":
    main()

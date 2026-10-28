"""NH and Foundation use one explicit root without freezing runtime XDG defaults."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def evaluate(settings, check=True):
    expression = 'let f = builtins.getFlake ' + json.dumps("path:" + str(ROOT)) + ''';
      lib = f.inputs.nixpkgs.lib;
      result = lib.evalModules {
        modules = [
          (f.outPath + "/modules/home/construction/_config-root.nix")
          ({ lib, ... }: {
            options.xdg.configHome = lib.mkOption { type = lib.types.str; default = "/home/alice/.config"; };
            options.programs.nh.homeFlake = lib.mkOption { type = lib.types.str; };
            options.home.sessionVariables = lib.mkOption { type = lib.types.attrsOf lib.types.str; default = {}; };
          })
          SETTINGS
        ];
      };
      in {
        nh = result.config.programs.nh.homeFlake;
        environment = result.config.home.sessionVariables;
        resolvedPath = if lib.hasPrefix "path:" result.config.programs.nh.homeFlake then
          (builtins.parseFlakeRef result.config.programs.nh.homeFlake).path else null;
      }
    '''.replace("SETTINGS", settings)
    return subprocess.run(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expression],
                          text=True, capture_output=True, check=check)


def main():
    cases = (
        ("{}", "path:/home/alice/.config/home-manager", {}, "/home/alice/.config/home-manager"),
        ('{ xdg.configHome = "/custom config"; }', "path:/custom%20config/home-manager", {}, "/custom config/home-manager"),
        ('{ xdg.configHome = "/custom"; foundation.configRoot = "/explicit root"; }', "path:/explicit%20root", {"FINITE_HOME_FLAKE_PATH": "/explicit root"}, "/explicit root"),
        ('{ programs.nh.homeFlake = "github:owner/repo#user"; }', "github:owner/repo#user", {}, None),
    )
    for settings, nh, environment, resolved_path in cases:
        assert json.loads(evaluate(settings).stdout) == {"nh": nh, "environment": environment, "resolvedPath": resolved_path}, settings
    special = json.loads(evaluate('{ foundation.configRoot = "/custom config/a#b?c%25"; }').stdout)
    assert special["resolvedPath"] == "/custom config/a#b?c%25", special
    for invalid in ('"relative/path"', '""', '42', './.'):
        result = evaluate('{ foundation.configRoot = ' + invalid + '; }', check=False)
        assert result.returncode != 0 and "foundation.configRoot" in result.stderr, result.stderr
    expression = 'let f = builtins.getFlake ' + json.dumps("path:" + str(ROOT)) + ''';
      profile = builtins.fromJSON (builtins.readFile (f.outPath + "/profile.json"));
      home = f.lib.mkHomeConfiguration {
        inherit profile;
        modules = [{ xdg.configHome = "/var/home/finite/custom config"; foundation.configRoot = "/shared root/a#b"; }];
      };
      in {
        nh = (builtins.parseFlakeRef home.config.programs.nh.homeFlake).path;
        cli = home.config.home.sessionVariables.FINITE_HOME_FLAKE_PATH;
        stateVersion = home.config.home.stateVersion;
      }'''
    real = subprocess.check_output(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expression], text=True)
    assert json.loads(real) == {"nh": "/shared root/a#b", "cli": "/shared root/a#b", "stateVersion": "26.05"}, real
    print("Config roots: XDG default, shared explicit absolute path, no default environment override, NH-only override and invalid types", flush=True)


if __name__ == "__main__":
    main()

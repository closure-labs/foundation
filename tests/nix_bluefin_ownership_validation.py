"""Both Bluefin profiles defer stock CLI tools but preserve personal Nix choices."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ["bbrew", "ugrep", "uutils-coreutils"]


def main():
    for foundation in ("bluefin", "bluefin-dx"):
        for explicit in (False, True):
            profile = {"schema": 3, "foundation": foundation, "hardware": "generic-x86_64",
                       "roles": [], "packages": [],
                       "identity": {"username": "alice", "homeDirectory": "/home/alice"}}
            expression = 'let f = builtins.getFlake ' + json.dumps("path:" + str(ROOT)) + ''';
              lib = f.inputs.nixpkgs.lib;
              profile = builtins.fromJSON PROFILE;
              home = f.lib.mkHomeConfiguration {
                inherit profile;
                modules = MODULES;
              };
              names = map lib.getName home.config.home.packages;
            in {
              tools = builtins.filter (name: builtins.elem name ["bbrew" "ugrep" "uutils-coreutils"]) names;
              preparation = lib.hasInfix "foundation-prepare" home.config.home.extraBuilderCommands;
              shell = lib.hasInfix "/home/linuxbrew/.linuxbrew/bin/fzf --zsh" home.config.programs.zsh.initContent;
              stateVersion = home.config.home.stateVersion;
            }'''.replace("PROFILE", json.dumps(json.dumps(profile))).replace("MODULES", '''[
              ({ pkgs, foundationPackageSets, ... }: {
                home.packages = [ foundationPackageSets.nixpkgs-unstable.bbrew pkgs.ugrep pkgs.uutils-coreutils ];
              })
            ]''' if explicit else "[]")
            result = json.loads(subprocess.check_output([
                "nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expression,
            ], text=True))
            assert sorted(result["tools"]) == (TOOLS if explicit else []), (foundation, explicit, result)
            assert result["preparation"] and result["shell"], result
            assert result["stateVersion"] == "26.05", result
    print("Bluefin ownership: both profiles omit automatic stock CLI duplicates and retain explicit personal packages/integration", flush=True)


if __name__ == "__main__":
    main()

"""Exercise real locked target resolution without downloads or activation.

Run from tests/nix-check.sh; unlike the offline fixtures this needs a Nix daemon.
"""
import copy
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from test_home import ROOT, home
from test_profile_validation import profile


def target(directory, *, normalizer, candidate=False):
    directory.mkdir()
    for name in ("catalog.nix", "home-catalog.nix", "normalize-profile.nix", "profile-capabilities.json"):
        shutil.copyfile(ROOT / "lib" / name, directory / name)
    extension = '''// {
      rolesByName = base.rolesByName // { future = { name = "future"; label = "Future"; order = 5; }; };
      roleNames = ["future"] ++ base.roleNames;
    }''' if candidate else ""
    directory.joinpath("flake.nix").write_text('''{
      outputs = _: let
        lib = {
          inherit (builtins) mapAttrs;
          genAttrs = names: f: builtins.listToAttrs (map (name: { inherit name; value = f name; }) names);
        };
        base = import ./catalog.nix;
        catalog = base EXTENSION;
      in { lib = {
        homeCatalog = import ./home-catalog.nix { domainCatalog = catalog; inherit lib; version = "fixture"; };
        CAPABILITIES
        NORMALIZER
      }; };
    }'''.replace("EXTENSION", extension).replace("CAPABILITIES", "profileCapabilities = builtins.fromJSON (builtins.readFile ./profile-capabilities.json);" if normalizer else "").replace("NORMALIZER", "normalizeProfile = import ./normalize-profile.nix { inherit catalog; };" if normalizer else ""))


def main():
    with tempfile.TemporaryDirectory(prefix="foundation-nix-validation-") as temporary:
        base = Path(temporary)
        # Deliberately stale and unusable: staged validation must never read it.
        def quiet_run(command, **kwargs):
            return subprocess.run(command, check=True, text=True, stderr=subprocess.PIPE, **kwargs)
        with patch.object(home, "run", side_effect=quiet_run), patch.dict(os.environ, FINITE_FOUNDATION_CATALOG=str(base / "missing-caller-catalog"),
                                                                        FINITE_RUNNING_PROFILE_PATH=str(base / "no-running-image")):
            for name, normalizer, candidate in (("legacy", False, False), ("bridge", True, False), ("candidate", True, True)):
                selected = base / name
                target(selected, normalizer=normalizer, candidate=candidate)
                stage = base / (name + "-consumer")
                stage.mkdir()
                stage.joinpath("flake.nix").write_text('''{
                  inputs.foundation.url = URL;
                  # A misleading caller catalog must not override the input's API.
                  outputs = _: { lib.homeCatalog = throw "used consumer catalog"; };
                }'''.replace("URL", home.nix_value("path:" + str(selected))))
                value = profile()
                if candidate:
                    value["roles"].append("future")
                home.write_json(stage / "profile.json", value)
                home.run(["nix", "flake", "lock", "path:" + str(stage)])
                lock_bytes = stage.joinpath("flake.lock").read_bytes()
                selected_bytes = selected.joinpath("flake.nix").read_bytes()
                # Mutable local inputs must still obey their locked content hash.
                selected.joinpath("flake.nix").write_text('{ outputs = _: throw "used unlocked input"; }')
                try:
                    home.validate_staged_profile(stage)
                except subprocess.CalledProcessError:
                    pass
                else:
                    raise AssertionError(f"{name} accepted changed locked source")
                selected.joinpath("flake.nix").write_bytes(selected_bytes)
                actual = home.validate_staged_profile(stage)
                expected = copy.deepcopy(value)
                expected.update(roles=(["future"] if candidate else []) + ["developer", "it"], packages=["jj", "uv"])
                assert actual == expected, (name, actual)
                assert stage.joinpath("flake.lock").read_bytes() == lock_bytes
                assert home.read_json(stage / "profile.json") == value
                value["roles"] = ["missing"]
                home.write_json(stage / "profile.json", value)
                try:
                    home.validate_staged_profile(stage)
                except (ValueError, subprocess.CalledProcessError):
                    pass
                else:
                    raise AssertionError(f"{name} accepted an unknown role")
                print(f"Locked {name} target normalization and rejection passed", flush=True)

            # Legacy generated standalone flakes use their own lib API.
            standalone = base / "standalone"
            target(standalone, normalizer=True)
            home.write_json(standalone / "profile.json", profile())
            home.run(["nix", "flake", "lock", "path:" + str(standalone)])
            assert home.validate_staged_profile(standalone)["roles"] == ["developer", "it"]
            print("Standalone target normalization passed", flush=True)

            for name, capabilities in (("unsupported", {"schema": 1, "initializeSchemas": [3], "normalizeSchemas": [3], "writeSchema": 3, "catalogSchemas": [3]}),
                                       ("malformed", None)):
                selected = base / (name + "-capabilities")
                target(selected, normalizer=True)
                home.write_json(selected / "profile-capabilities.json", capabilities)
                home.write_json(selected / "profile.json", profile())
                home.run(["nix", "flake", "lock", "path:" + str(selected)])
                with patch.object(home, "validate_profile") as fallback:
                    try:
                        home.validate_staged_profile(selected)
                    except (ValueError, subprocess.CalledProcessError):
                        pass
                    else:
                        raise AssertionError(f"Accepted {name} target capabilities")
                    fallback.assert_not_called()
                print(f"Explicit {name} target capabilities rejected without fallback", flush=True)

            # Check the actual public export, rather than only the fixture API.
            expression = 'let f = builtins.getFlake ' + home.nix_value("path:" + str(ROOT)) + '; in f.lib.normalizeProfile '
            expression += '(builtins.fromJSON ' + home.nix_value(json.dumps(profile())) + ')'
            actual = json.loads(home.capture(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expression]))
            assert actual["roles"] == ["developer", "it"]
            print("Foundation public normalization export passed", flush=True)

            expression = 'import ' + str(ROOT / "tests/draft-providers.nix") + ' { foundation = builtins.getFlake '
            expression += home.nix_value("path:" + str(ROOT)) + '; }'
            providers = json.loads(home.capture(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expression]))
            assert providers and all(app["available"] for app in providers.values()), providers
            print(f"All {len(providers)} draft Nix providers exist in the locked inputs (no builds)", flush=True)


if __name__ == "__main__":
    main()

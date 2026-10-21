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


def target(directory, *, normalizer, candidate=False, descriptor=True):
    directory.mkdir()
    for name in ("catalog.nix", "home-catalog.nix", "normalize-profile.nix", "normalize-profile-v2.nix", "hosts.nix", "profile-capabilities.json"):
        shutil.copyfile(ROOT / "lib" / name, directory / name)
    shutil.copytree(ROOT / "lib/profile-drafts", directory / "profile-drafts")
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
    }'''.replace("EXTENSION", extension).replace("CAPABILITIES", "profileCapabilities = builtins.fromJSON (builtins.readFile ./profile-capabilities.json);" if normalizer and descriptor else "").replace("NORMALIZER", "normalizeProfile = import ./normalize-profile.nix { inherit catalog; };" if normalizer else ""))


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

                if normalizer and not candidate:
                    value = {**profile(), "schema": 3, "roles": ["creative", "family"],
                             "capabilities": ["recording"], "custom": {"preserve": True}}
                    home.write_json(stage / "profile.json", value)
                    actual = home.validate_staged_profile(stage)
                    assert actual == {**value, "roles": ["family", "creative"], "packages": ["jj", "uv"],
                        "host": {"system": "x86_64-linux", "formFactor": "generic", "cpu": "generic", "gpus": [],
                                 "model": "generic", "camera": False, "fingerprint": False}}
                    assert home.read_json(stage / "profile.json") == value
                    assert stage.joinpath("flake.lock").read_bytes() == lock_bytes
                    print("Locked schema-3 reader preserves capabilities/extensions without writing", flush=True)

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

            expression = '''let f = builtins.getFlake ''' + home.nix_value("path:" + str(ROOT)) + ''';
              domain = f.lib.catalog;
              withImages = domain // {
                foundationsByName = builtins.mapAttrs (name: value: value // {
                  profiles.generic-x86_64.name = if name == "bluefin" then "finite" else "finite-dev";
                }) domain.foundationsByName;
              };
              legacyDomain = builtins.removeAttrs domain ["classifications"] // {
                rolesByName = builtins.mapAttrs (_: role: builtins.removeAttrs role ["classification"]) domain.rolesByName;
              };
            in {
              default = f.lib.homeCatalog;
              legacy = f.lib.homeCatalogForSchema 2;
              current = f.lib.homeCatalogForSchema 3;
              custom = f.lib.mkHomeCatalog { domainCatalog = withImages; };
              customLegacy = f.lib.mkHomeCatalog { domainCatalog = legacyDomain; schema = 2; };
              applications = builtins.fromJSON (builtins.readFile (f.lib.mkApplications {pkgs = f.inputs.nixpkgs.legacyPackages.x86_64-linux;}).profileCatalog);
              packaged = builtins.fromJSON (builtins.readFile f.packages.x86_64-linux.home-profile-catalog);
            }'''
            catalogs = json.loads(home.capture(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expression]))
            assert catalogs["default"] == catalogs["current"]
            assert len(catalogs["legacy"]["roles"]) == 6
            assert len(catalogs["current"]["roles"]) == 10
            assert len(catalogs["current"]["capabilities"]) == 31
            assert catalogs["current"]["profileCapabilities"]["writeSchema"] == 3
            assert catalogs["default"] == catalogs["applications"] == catalogs["packaged"]
            assert catalogs["custom"]["foundations"]["bluefin"]["profiles"] == {"generic-x86_64": "finite"}
            assert catalogs["custom"]["classifications"]["personal"]["roles"] == ["family", "media", "creative", "gaming"]
            assert catalogs["customLegacy"]["classifications"] == {}
            assert len(catalogs["customLegacy"]["roles"]) == 6
            assert all(role["classification"] is None for role in catalogs["customLegacy"]["roles"].values())
            print("API/application/package catalogs agree; schema-3 image mappings and explicit legacy custom constructor pass", flush=True)

            selected = base / "old-schema2-source"
            target(selected, normalizer=True)
            selected.joinpath("normalize-profile.nix").write_text((ROOT / "lib/normalize-profile-v2.nix").read_text())
            home.write_json(selected / "profile-capabilities.json", {**home.profile_capabilities(), "initializeSchemas": [1, 2], "normalizeSchemas": [2], "writeSchema": 2})
            home.write_json(selected / "profile.json", {**profile(), "schema": 3, "capabilities": []})
            home.run(["nix", "flake", "lock", "path:" + str(selected)])
            before = home.tree_digest(selected)
            try:
                home.validate_staged_profile(selected)
            except subprocess.CalledProcessError:
                pass
            else:
                raise AssertionError("Old schema-2 source accepted schema 3")
            assert home.tree_digest(selected) == before
            print("New helper rejects supplied schema 3 against a schema-2-only source without writes", flush=True)

            selected = base / "descriptor-absent-source"
            target(selected, normalizer=True, descriptor=False)
            home.write_json(selected / "profile.json", {**profile(), "schema": 3, "capabilities": []})
            home.run(["nix", "flake", "lock", "path:" + str(selected)])
            before = home.tree_digest(selected)
            try:
                home.validate_staged_profile(selected)
            except subprocess.CalledProcessError:
                pass
            else:
                raise AssertionError("Descriptor-absent target implied schema-3 support")
            assert home.tree_digest(selected) == before
            print("Schema-3 normalizer without explicit capabilities rejected without writes", flush=True)

            expression = 'import ' + str(ROOT / "tests/draft-providers.nix") + ' { foundation = builtins.getFlake '
            expression += home.nix_value("path:" + str(ROOT)) + '; }'
            providers = json.loads(home.capture(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expression]))
            assert providers and all(app["available"] for app in providers.values()), providers
            print(f"All {len(providers)} draft Nix providers exist in the locked inputs (no builds)", flush=True)


if __name__ == "__main__":
    main()

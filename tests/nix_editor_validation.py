"""Exercise the real locked editor API without building or activating a home."""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from test_home import ROOT, home, INFO
from test_profile_validation import profile


def main():
    with tempfile.TemporaryDirectory(prefix="foundation-locked-editor-") as temporary:
        base = Path(temporary)
        source = base / "selected-source"
        source.mkdir()
        # Copy only the pure API so old/new capability cases are independent of
        # package builds, mutable caller catalogs or the test host's account.
        shutil.copytree(ROOT / "lib", source / "lib")
        source.joinpath("flake.nix").write_text('''{
          outputs = _: let
            lib = { inherit (builtins) mapAttrs; genAttrs = names: f: builtins.listToAttrs (map (name: {inherit name; value=f name;}) names); };
            catalog = import ./lib/catalog.nix;
            composition = import ./lib/profile-drafts {inherit catalog;};
            project = domainCatalog: import ./lib/home-catalog.nix {inherit domainCatalog lib; version="fixture";};
          in {lib = {
            homeCatalog = project catalog;
            homeCatalogForSchema = schema: if schema == 2 then project catalog else
              (project (catalog // {rolesByName=composition.contract.roles; roleNames=builtins.attrNames composition.contract.roles;})) //
              {profileSchema=3; capabilities=composition.contract.capabilities;};
            normalizeProfile = import ./lib/normalize-profile.nix {inherit catalog;};
            profileCapabilities = builtins.fromJSON (builtins.readFile ./lib/profile-capabilities.json);
            profileChanges = {schema=1; preview=import ./lib/profile-changes.nix {inherit catalog;};};
          };};
        }''')
        root = base / "home-manager"
        root.mkdir()
        root.joinpath("flake.nix").write_text('{ inputs.foundation.url = ' + home.nix_value("path:" + str(source)) + '; outputs = _: {}; }')
        home.write_json(root / "profile.json", {**profile(), "custom": {"preserve": True}})
        root.joinpath("customize.nix").write_text("{}")
        home.run(["nix", "flake", "lock", "path:" + str(root)])
        original = home.tree_digest(root)
        environment = {"FINITE_RUNNING_PROFILE_PATH": str(base / "no-running-image"), "FINITE_FOUNDATION_CATALOG": "/caller/stale/catalog.json"}
        with patch.dict(os.environ, environment), patch.object(home, "build") as build, patch.object(home, "provision_brew") as brew, patch.object(home, "commit_stage") as commit:
            context = home.read_editor(root, migrate=True)
            assert context["profile"]["schema"] == 2
            assert len(context["catalog"]["roles"]) == 10
            assert context["canMigrate"] is True
            review = home.apply(root, roles="family,creative", packages="", capabilities="recording", migrate_profile=True, preview=True)
            assert review["preview"]["candidate"]["schema"] == 3
            assert review["preview"]["source"]["packages"] == ["jj", "uv"]
            assert review["preview"]["candidate"]["packages"] == []
            assert review["preview"]["candidate"]["custom"] == {"preserve": True}
            assert review["source"]["path"].startswith("/nix/store/")
            assert review == home.apply(root, roles="family,creative", packages="", capabilities="recording", migrate_profile=True, preview=True)
            assert home.tree_digest(root) == original
            assert not (base / ".foundation.lock").exists()
            build.assert_not_called(); brew.assert_not_called(); commit.assert_not_called()
        print("Locked target editor/candidate-only package preview passed; caller catalog ignored and no live writes", flush=True)

        # Build-only exercises the same controller candidate and negotiation;
        # the build boundary is replaced, never an actual GUI package build.
        with patch.dict(os.environ, environment), patch.object(home, "installed_info", return_value=INFO), patch.object(home, "build") as build, patch.object(home, "provision_brew") as brew:
            home.apply(root, roles="family,creative", packages="", capabilities="recording", migrate_profile=True,
                       approve_preview=review["approvalToken"], check=True)
            build.assert_called_once(); brew.assert_not_called()
            assert home.tree_digest(root) == original
        print("Actual locked editor preview token matches separate staged build-only invocation", flush=True)

        for mode in ("old-reader", "future-editor"):
            selected = base / mode
            shutil.copytree(source, selected)
            capabilities = home.read_json(selected / "lib/profile-capabilities.json")
            capabilities.pop("editSchemas")
            home.write_json(selected / "lib/profile-capabilities.json", capabilities)
            if mode == "future-editor":
                selected.joinpath("flake.nix").write_text(selected.joinpath("flake.nix").read_text().replace("profileChanges = {schema=1;", "profileChanges = {schema=2;"))
                capabilities["editSchemas"] = [2, 3]
                home.write_json(selected / "lib/profile-capabilities.json", capabilities)
            consumer = base / (mode + "-consumer")
            consumer.mkdir()
            consumer.joinpath("flake.nix").write_text('{inputs.foundation.url=' + home.nix_value("path:" + str(selected)) + '; outputs=_: {}; }')
            home.write_json(consumer / "profile.json", profile())
            home.run(["nix", "flake", "lock", "path:" + str(consumer)])
            before = home.tree_digest(consumer)
            with patch.dict(os.environ, environment):
                assert home.read_editor(consumer)["profile"]["schema"] == 2
                try:
                    home.read_editor(consumer, migrate=True)
                except subprocess.CalledProcessError:
                    pass
                else:
                    raise AssertionError(f"Accepted incompatible {mode}")
            assert home.tree_digest(consumer) == before
            print(f"{mode} rejects new editing while retaining schema-2 catalog compatibility", flush=True)

        expression = 'let f = builtins.getFlake ' + home.nix_value("path:" + str(ROOT)) + '; in { schema = f.lib.profileChanges.schema; preview = f.lib.profileChanges.preview '
        expression += home.nix_value({"profile": profile(), "migrate": True, "roles": ["family"], "packages": []}) + '; }'
        data = json.loads(home.capture(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expression]))
        assert data["schema"] == 1 and data["preview"]["candidate"]["schema"] == 3
        print("Actual Foundation public profileChanges export passed", flush=True)


if __name__ == "__main__":
    def quiet_run(command, **kwargs):
        return subprocess.run(command, check=True, text=True, stderr=subprocess.PIPE, **kwargs)
    try:
        with patch.object(home, "run", side_effect=quiet_run):
            main()
    except subprocess.CalledProcessError as error:
        print(error.stderr)
        raise

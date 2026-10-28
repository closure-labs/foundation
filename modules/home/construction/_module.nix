{
  den,
  inputs,
  lib,
  foundationProfile ? builtins.fromJSON (builtins.readFile ../../../profile.json),
  foundationModules ? [../../../customize.nix ../../local.nix],
  foundationPackagePolicy ? {},
  ...
}: let
  # The version-controlled profile selects the account, roles and packages.
  vars = (import ../../../lib/normalize-profile.nix {inherit catalog;}) foundationProfile;
  system = vars.host.system;
  catalog = import ../../../lib/catalog.nix;
  canonicalRoles = vars.roles;
  canonicalPackages = vars.packages;
  composition = (import ../../../lib/profile-drafts {inherit catalog;}).resolve vars;
  packageSets = import ../../providers/nixpkgs/_package-sets.nix {
    inherit inputs system;
    packagePolicy = foundationPackagePolicy;
  };
  pkgs = packageSets.nixpkgs;
  applications = import ../../../lib/applications.nix {
    inherit pkgs;
    source = ../../..;
  };

in {
  imports = [./_aspects.nix];
  den.homes.${system}.${vars.identity.username} = {
    userName = vars.identity.username;
    inherit pkgs;
    aspect = den.aspects.finite-home;
    instantiate = {
      modules,
      pkgs,
      ...
    }:
      inputs.home-manager.lib.homeManagerConfiguration {
        inherit modules pkgs;
        extraSpecialArgs = {
          inherit inputs;
          foundationPackageSets = packageSets;
          foundationHost = vars.host;
          foundationComposition = composition;
          finiteHomeAssets = {
            devops = ../../capabilities/devops/_assets/rootfs/usr/share/finite;
          };
        };
      };
  };

  den.aspects = {
    finite-home = {
      includes = map (id: den.aspects.foundation.${id})
        (import ../../profiles/composition/_selection.nix vars).roots;
      homeManager = { config, ... }: {
        assertions = [{
          assertion = let
            loader = import ../../flake/features/_loader.nix {};
            selection = import ../../profiles/composition/_selection.nix vars;
          in builtins.sort builtins.lessThan config.foundation.featureIds
            == builtins.sort builtins.lessThan (loader.closure selection.schema selection.roots);
          message = "Resolved Den membership differs from the declared dependency graph";
        }];
        home = {
          username = lib.mkForce vars.identity.username;
          homeDirectory = lib.mkForce vars.identity.homeDirectory;
          packages = [applications.foundation];
          sessionVariables = {
            FINITE_FOUNDATION = vars.foundation;
            FINITE_HARDWARE = vars.hardware;
            FINITE_PACKAGES = lib.concatStringsSep "," canonicalPackages;
            FINITE_ROLES = lib.concatStringsSep "," canonicalRoles;
          };
        };
        imports = foundationModules ++ [./_config-root.nix];
      };
    };
  };
}

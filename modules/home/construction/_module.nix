{
  den,
  inputs,
  lib,
  foundationProfile ? builtins.fromJSON (builtins.readFile ../../../profile.json),
  foundationModules ? [../../../customize.nix ../../local.nix],
  ...
}: let
  # The version-controlled profile selects the account, roles and packages.
  vars = (import ../../../lib/normalize-profile.nix {inherit catalog;}) foundationProfile;
  system =
    if vars.schema == 3
    then vars.host.system
    else "x86_64-linux";
  catalog = import ../../../lib/catalog.nix;
  canonicalRoles = vars.roles;
  canonicalPackages = vars.packages;
  composition =
    if vars.schema == 3
    then (import ../../../lib/profile-drafts {inherit catalog;}).resolve vars
    else null;
  pkgs = import inputs.nixpkgs {
    inherit system;
    config.allowUnfree = true;
  };
  selectedPackages = map (import ../../profiles/composition/_legacy-packages.nix { inherit inputs pkgs; }) canonicalPackages;
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
          foundationProfileSchema = vars.schema;
          foundationHost =
            if vars.schema == 3
            then vars.host
            else null;
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
          packages =
            [applications.foundation]
            ++ lib.optionals (vars.schema == 2) selectedPackages;
          sessionVariables = {
            FINITE_FOUNDATION = vars.foundation;
            FINITE_HARDWARE = vars.hardware;
            FINITE_PACKAGES = lib.concatStringsSep "," canonicalPackages;
            FINITE_ROLES = lib.concatStringsSep "," canonicalRoles;
          };
        };
        imports = foundationModules;
        programs = {
          nh.homeFlake = "path:${vars.identity.homeDirectory}/.config/home-manager";
        };
      };
    };
  };
}

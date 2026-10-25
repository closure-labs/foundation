{
  den,
  inputs,
  lib,
  foundationProfile ? builtins.fromJSON (builtins.readFile ../../profile.json),
  foundationModules ? [../../customize.nix ../local.nix],
  ...
}: let
  # The version-controlled profile selects the account, roles and packages.
  vars = (import ../../lib/normalize-profile.nix {inherit catalog;}) foundationProfile;
  system =
    if vars.schema == 3
    then vars.host.system
    else "x86_64-linux";
  catalog = import ../../lib/catalog.nix;
  canonicalRoles = vars.roles;
  canonicalPackages = vars.packages;
  composition =
    if vars.schema == 3
    then (import ../../lib/profile-drafts {inherit catalog;}).resolve vars
    else null;
  pkgs = import inputs.nixpkgs {
    inherit system;
    config.allowUnfree = true;
  };
  unstable = inputs.nixpkgs-unstable.legacyPackages.${system};
  optionalPackages = {
    "hack-font" = pkgs.nerd-fonts.hack;
    inherit (unstable) herdr;
    jj = pkgs.jujutsu;
    inherit (pkgs) opencode uv;
  };
  selectedPackages = map (name: optionalPackages.${name}) canonicalPackages;
  applications = import ../../lib/applications.nix {
    inherit pkgs;
    source = ../..;
  };
  homeApply = applications.homeApply;
  configure = pkgs.writeShellApplication {
    name = "finite-configure";
    runtimeInputs = with pkgs; [coreutils jq zenity homeApply];
    runtimeEnv.FINITE_FOUNDATION_CATALOG = applications.profileCatalog;
    text = builtins.readFile ./finite-configure;
  };
in {
  imports = [./aspects.nix];
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
            devops = ./aspects/capabilities/devops/rootfs/usr/share/finite;
          };
        };
      };
  };

  den.aspects = {
    finite-home = {
      includes =
        [den.aspects.features.base]
        ++ (
          if vars.schema == 2
          then map (role: den.aspects.features.roles.${role}) canonicalRoles
          else
            [den.aspects.features.profile-composition]
            ++ lib.optional (builtins.elem "devops" composition.effectiveCapabilities) den.aspects.features.capabilities.devops
        )
        ++ (
          if vars.schema == 3
          then
            [
              den.aspects.features.host
              den.aspects.features.machines.${vars.host.formFactor}
              den.aspects.features.hardware.cpu.${vars.host.cpu}
              den.aspects.features.hardware.models.${vars.host.model}
            ]
            ++ map (gpu: den.aspects.features.hardware.gpu.${gpu}) vars.host.gpus
          else [den.aspects.features.hardware.${vars.hardware}]
        );
      homeManager = {
        home = {
          username = lib.mkForce vars.identity.username;
          homeDirectory = lib.mkForce vars.identity.homeDirectory;
          packages =
            [configure homeApply applications.homeUpdate applications.homeMigrate applications.appStatus]
            ++ lib.optionals (vars.schema == 2) selectedPackages;
          sessionVariables = {
            FINITE_FOUNDATION = vars.foundation;
            FINITE_HARDWARE = vars.hardware;
            FINITE_PACKAGES = lib.concatStringsSep "," canonicalPackages;
            FINITE_ROLES = lib.concatStringsSep "," canonicalRoles;
          };
        };
        imports = [./compat/nix-profile-command.nix] ++ foundationModules;
        programs = {
          nh.homeFlake = "path:${vars.identity.homeDirectory}/.config/home-manager";
          zsh.shellAliases.finite-configure = "${configure}/bin/finite-configure";
        };
      };
    };
  };
}

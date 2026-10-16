{
  den,
  inputs,
  lib,
  foundationProfile ? builtins.fromJSON (builtins.readFile ../profile.json),
  foundationModules ? [../customize.nix ./local.nix],
  ...
}: let
  # The version-controlled profile selects the account, roles and packages.
  vars = foundationProfile;
  system = "x86_64-linux";
  catalog = import ../lib/catalog.nix;
  roleOrder = catalog.roleNames;
  packageOrder = catalog.packageNames;
  hardwareNames = catalog.homeHardwareNames;
  canonicalRoles = builtins.filter (role: builtins.elem role vars.roles) roleOrder;
  canonicalPackages = builtins.filter (package: builtins.elem package vars.packages) packageOrder;
  validProfile =
    vars.schema
    == 2
    && builtins.elem vars.foundation ["bluefin" "bluefin-dx"]
    && builtins.elem vars.hardware hardwareNames
    && builtins.length vars.roles == builtins.length canonicalRoles
    && builtins.length vars.roles == builtins.length (lib.unique vars.roles)
    && builtins.length vars.packages == builtins.length canonicalPackages
    && builtins.length vars.packages == builtins.length (lib.unique vars.packages)
    && builtins.match "[a-z_][a-z0-9_-]*[$]?" vars.identity.username != null
    && builtins.match "/.+" vars.identity.homeDirectory != null;
  pkgs = import inputs.nixpkgs {
    inherit system;
    config.allowUnfree = true;
  };
  weekly = inputs.nixpkgs-weekly.legacyPackages.${system};
  optionalPackages = {
    "hack-font" = pkgs.nerd-fonts.hack;
    inherit (weekly) herdr;
    jj = pkgs.jujutsu;
    inherit (pkgs) opencode uv;
  };
  selectedPackages = map (name: optionalPackages.${name}) canonicalPackages;
  applications = import ../lib/applications.nix {
    inherit pkgs;
    source = ../.;
  };
  homeApply = applications.homeApply;
  configure = pkgs.writeShellApplication {
    name = "finite-configure";
    runtimeInputs = with pkgs; [coreutils jq zenity homeApply];
    text = builtins.readFile ./finite-configure;
  };
in
  if !validProfile
  then throw "The local Finite profile is invalid or is not canonically ordered."
  else {
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
          ++ map (role: den.aspects.features.roles.${role}) canonicalRoles
          ++ [den.aspects.features.hardware.${vars.hardware}];
        homeManager = {
          home = {
            username = lib.mkForce vars.identity.username;
            homeDirectory = lib.mkForce vars.identity.homeDirectory;
            packages = [configure homeApply applications.homeUpdate applications.homeMigrate applications.appStatus] ++ selectedPackages;
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

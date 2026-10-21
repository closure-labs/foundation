# Schema-3 application membership comes from the shared pure resolver.
{
  config,
  inputs,
  lib,
  pkgs,
  foundationComposition,
  ...
}: let
  plan = foundationComposition;
  system = pkgs.stdenv.hostPlatform.system;
  sources = {
    nixpkgs = pkgs;
    nixpkgs-weekly = inputs.nixpkgs-weekly.legacyPackages.${system};
    nixpkgs-unstable = inputs.nixpkgs-unstable.legacyPackages.${system};
    devenv = inputs.devenv.packages.${system};
  };
  packageFor = name: let
    app = plan.applications.${name};
    package =
      if (app.recipe or null) == "finite-ghostty"
      then import ../../lib/ghostty-package.nix {inherit pkgs;}
      else lib.getAttrFromPath (lib.splitString "." app.attribute) sources.${app.input};
    wrapped = config.lib.nixGL.wrap package;
  in
    if app.graphical
    then
      if app.removeIconBuildFiles or false
      then
        import ../../lib/without-icon-build-files.nix {
          inherit pkgs;
          package = wrapped;
        }
      else wrapped
    else package;
  nixIds = builtins.filter (name: plan.applications.${name}.provider == "nix" && name != "firefox") plan.applicationIds;
  flatpakIds = builtins.filter (name: plan.applications.${name}.provider == "flatpak") plan.applicationIds;
  has = name: builtins.elem name plan.effectiveCapabilities;
  support = import ./roles/support/home.nix {inherit pkgs;};
  trainer = import ./roles/trainer/home.nix {};
  executive = import ./roles/executive/home.nix {};
in {
  home.packages = map packageFor nixIds;
  home.sessionVariables = lib.genAttrs (map (role: "FINITE_ROLE_${lib.toUpper role}") plan.profile.roles) (_: "1");
  services.flatpak.packages = map (name: plan.applications.${name}.id) flatpakIds;
  systemd.user.services = lib.optionalAttrs (has "support-tools") support.systemd.user.services;
  xdg.desktopEntries =
    lib.optionalAttrs (has "trainer-links") trainer.xdg.desktopEntries
    // lib.optionalAttrs (has "executive-links") executive.xdg.desktopEntries;
}

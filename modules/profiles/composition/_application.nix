{ id, application }: { config, inputs, lib, pkgs, foundationComposition, ... }: let
  app = application;
  sources = {
    nixpkgs = pkgs;
    nixpkgs-weekly = inputs.nixpkgs-weekly.legacyPackages.${pkgs.stdenv.hostPlatform.system};
    nixpkgs-unstable = inputs.nixpkgs-unstable.legacyPackages.${pkgs.stdenv.hostPlatform.system};
    devenv = inputs.devenv.packages.${pkgs.stdenv.hostPlatform.system};
  };
  raw = if (app.recipe or null) == "finite-ghostty"
    then import ../../apps/ghostty/_package.nix { inherit pkgs; }
    else lib.getAttrFromPath (lib.splitString "." app.attribute) sources.${app.input};
  wrapped = if app.graphical then config.lib.nixGL.wrap raw else raw;
  package = if app.removeIconBuildFiles or false then
    import ../../providers/graphics/_without-icon-build-files.nix { inherit pkgs; package = wrapped; } else wrapped;
  index = builtins.length (builtins.filter (name: name < id) foundationComposition.applicationIds);
in {
  home.packages = lib.mkIf (app.provider == "nix" && id != "firefox") (lib.mkOrder (800 + index) [package]);
  services.flatpak.packages = lib.mkIf (app.provider == "flatpak") (lib.mkOrder (1000 + index) [app.id]);
}

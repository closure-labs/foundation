{ id, application }: args@{ config, inputs, lib, pkgs, foundationComposition, ... }: let
  app = application;
  packageSets = args.foundationPackageSets or (import ../../providers/nixpkgs/_package-sets.nix {
    inherit inputs;
    system = pkgs.stdenv.hostPlatform.system;
  });
  sources = packageSets // {
    nixpkgs = pkgs;
    devenv = inputs.devenv.packages.${pkgs.stdenv.hostPlatform.system};
  };
  source =
    if app.input == "ai"
    then inputs.${app.pin}.packages.${pkgs.stdenv.hostPlatform.system}
    else sources.${app.pin or app.input};
  raw = if (app.recipe or null) == "finite-ghostty"
    then import ../../apps/ghostty/_package.nix { inherit pkgs; }
    else lib.getAttrFromPath (lib.splitString "." app.attribute) source;
  licensed = if app.input == "ai" && lib.any (license: !(license.free or true))
    (lib.toList (raw.meta.license or []))
    then assert pkgs.config.allowUnfree || pkgs.config.allowUnfreePredicate raw; raw
    else raw;
  configured = if (app.recipe or null) == "zoom-gnome-media-keys"
    then licensed.override {targetPkgs = p: [p.gnome-settings-daemon];}
    else licensed;
  wrapped = if app.graphical then config.lib.nixGL.wrap configured else configured;
  package = if app.removeIconBuildFiles or false then
    import ../../providers/graphics/_without-icon-build-files.nix { inherit pkgs; package = wrapped; } else wrapped;
  index = builtins.length (builtins.filter (name: name < id) foundationComposition.applicationIds);
in {
  home.packages = lib.mkIf (app.provider == "nix" && id != "firefox") (lib.mkOrder (800 + index) [package]);
  services.flatpak.packages = lib.mkIf (app.provider == "flatpak") (lib.mkOrder (1000 + index) [app.id]);
}

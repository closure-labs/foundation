{
  foundation,
  profile,
}: let
  inherit (foundation.lib.inputs.nixpkgs) lib;
  home = foundation.lib.mkHomeConfiguration {inherit profile;};
  c = home.config;
  plan = foundation.lib.resolveProfile profile;
  sources = (import ../modules/providers/nixpkgs/_package-sets.nix {
    inputs = foundation.lib.inputs;
    system = "x86_64-linux";
  }) // {
    nixpkgs = home.pkgs;
    devenv = foundation.lib.inputs.devenv.packages.x86_64-linux;
  };
  installed = map (p: p.outPath) c.home.packages;
  expectedFirefox = sources.nixpkgs-unstable.firefox.override {
    extraPolicies = lib.optionalAttrs (plan.profile.host.model == "dell-xps-9350" && plan.profile.host.camera) {
      Preferences."media.webrtc.camera.allow-pipewire" = {
        Value = true;
        Status = "locked";
      };
    };
  };
  nixApps = lib.filterAttrs (name: app: app.provider == "nix" && name != "firefox") plan.applications;
  packages =
    lib.mapAttrs (_: app: let
      raw =
        if (app.recipe or null) == "finite-ghostty"
        then import ../modules/apps/ghostty/_package.nix {pkgs = home.pkgs;}
        else if (app.recipe or null) == "zoom-gnome-media-keys"
        then sources.nixpkgs-weekly.zoom-us.override {targetPkgs = p: [p.gnome-settings-daemon];}
        else if app.input == "ai"
        then foundation.lib.inputs.${app.pin}.packages.x86_64-linux.${app.attribute}
        else lib.getAttrFromPath (lib.splitString "." app.attribute) sources.${app.pin or app.input};
      expected =
        if app.graphical
        then
          if app.removeIconBuildFiles or false
          then
            import ../modules/providers/graphics/_without-icon-build-files.nix {
              pkgs = home.pkgs;
              package = c.lib.nixGL.wrap raw;
            }
          else c.lib.nixGL.wrap raw
        else raw;
    in {
      installedOnce = builtins.length (builtins.filter (path: path == expected.outPath) installed) == 1;
      rawAbsent = !app.graphical || !(builtins.elem raw.outPath installed);
      wrapperUsesNixGL = !app.graphical || lib.hasInfix "nixGLCombinedWrapper" expected.buildCommand;
    })
    nixApps;
in {
  drv = home.activationPackage.drvPath;
  inherit packages;
  homeManagerCliInstalled = builtins.elem c.programs.home-manager.package.outPath installed;
  gpu = c.targets.genericLinux.gpu.enable;
  nixgl = c.targets.genericLinux.nixGL.packages != null;
  vulkan = c.targets.genericLinux.nixGL.vulkan.enable;
  firefoxWrapped = lib.hasInfix "nixGLCombinedWrapper" c.programs.firefox.package.buildCommand;
  firefoxRecipePreserved = c.programs.firefox.package.outPath == (c.lib.nixGL.wrap expectedFirefox).outPath;
  flatpaks = c.services.flatpak.packages;
  environment = c.home.sessionVariables;
  services = builtins.attrNames c.systemd.user.services;
  desktopEntries = builtins.attrNames c.xdg.desktopEntries;
  ghosttyConfigured = builtins.hasAttr "ghostty/config.ghostty" c.xdg.configFile;
}

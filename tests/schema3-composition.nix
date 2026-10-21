{
  foundation,
  profile,
}: let
  inherit (foundation.inputs.nixpkgs) lib;
  home = foundation.lib.mkHomeConfiguration {inherit profile;};
  c = home.config;
  plan = foundation.lib.resolveProfile profile;
  sources = {
    nixpkgs = home.pkgs;
    nixpkgs-weekly = foundation.inputs.nixpkgs-weekly.legacyPackages.x86_64-linux;
    nixpkgs-unstable = foundation.inputs.nixpkgs-unstable.legacyPackages.x86_64-linux;
    devenv = foundation.inputs.devenv.packages.x86_64-linux;
  };
  installed = map (p: p.outPath) c.home.packages;
  expectedFirefox = sources.nixpkgs-weekly.firefox.override {
    extraPolicies = lib.optionalAttrs (profile.hardware == "dell-xps-9350-intel") {
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
        then import ../lib/ghostty-package.nix {pkgs = home.pkgs;}
        else lib.getAttrFromPath (lib.splitString "." app.attribute) sources.${app.input};
      expected =
        if app.graphical
        then c.lib.nixGL.wrap raw
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

{
  foundation,
  profile,
}: let
  home = foundation.lib.mkHomeConfiguration {inherit profile;};
  c = home.config;
in {
  drv = home.activationPackage.drvPath;
  host = builtins.fromJSON c.xdg.configFile."finite/host.json".text;
  environment = c.home.sessionVariables;
  services = builtins.attrNames c.systemd.user.services;
  files = builtins.attrNames c.xdg.configFile;
  batteryPercentage = c.dconf.settings."org/gnome/desktop/interface".show-battery-percentage or null;
  nixgl = c.targets.genericLinux.nixGL.packages != null;
  gpu = c.targets.genericLinux.gpu.enable;
  vulkan = c.targets.genericLinux.nixGL.vulkan.enable;
  firefox = c.programs.firefox.package.outPath;
  # Compare Firefox recipes to prove camera policy changes are model-scoped.
  expectedFirefox =
    (c.lib.nixGL.wrap (foundation.inputs.nixpkgs-weekly.legacyPackages.x86_64-linux.firefox.override {
      extraPolicies = foundation.inputs.nixpkgs.lib.optionalAttrs (c.home.sessionVariables.FINITE_HOST_MODEL == "dell-xps-9350" && c.home.sessionVariables.FINITE_HOST_CAMERA == "1") {
        Preferences."media.webrtc.camera.allow-pipewire" = {
          Value = true;
          Status = "locked";
        };
      };
    })).outPath;
  stateVersion = c.home.stateVersion;
  catalog = (foundation.lib.homeCatalogForSchema 3).hosts;
}

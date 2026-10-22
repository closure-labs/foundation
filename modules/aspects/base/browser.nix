{
  config,
  inputs,
  lib,
  pkgs,
  foundationProfileSchema ? 2,
  foundationHost ? null,
  ...
}: let
  system = pkgs.stdenv.hostPlatform.system;
  weekly = inputs.nixpkgs-weekly.legacyPackages.${system};
  pipewireCameraPolicies =
    # Upstream Firefox keeps the PipeWire camera backend disabled because it
    # replaces V4L2 without a reliable fallback. Restrict it to the Dell IPU7
    # hardware, whose usable libcamera source is exposed through PipeWire.
    lib.optionalAttrs
    (
      if foundationHost != null
      then foundationHost.model == "dell-xps-9350" && foundationHost.camera
      else (config.home.sessionVariables.FINITE_HARDWARE or "") == "dell-xps-9350-intel"
    )
    {
      Preferences."media.webrtc.camera.allow-pipewire" = {
        Value = true;
        Status = "locked";
      };
    };
  finiteFirefox = weekly.firefox.override {
    extraPolicies = pipewireCameraPolicies;
  };
in {
  programs = {
    firefox = {
      enable = true;
      package =
        if foundationProfileSchema == 3
        then config.lib.nixGL.wrap finiteFirefox
        else finiteFirefox;
    };
  };
}

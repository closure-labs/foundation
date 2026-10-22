{
  config,
  inputs,
  lib,
  foundationProfileSchema ? 2,
  ...
}: {
  fonts.fontconfig.enable = true;

  # A cold Flatpak install exceeded sd-switch's two-minute default in the VM.
  # Keep activation synchronous so installation failures still fail the switch.
  systemd.user.servicesStartTimeoutMs = 15 * 60 * 1000;

  # The generic-Linux default appends the manager's inherited value on every
  # reload, duplicating D-Bus service search paths. Use declared directories
  # and retain both Flatpak export locations without growing the variable.
  # Extend xdg.systemDirs.data to add paths; an explicit stronger override
  # can replace this value when a consumer needs full control.
  systemd.user.sessionVariables.XDG_DATA_DIRS = lib.mkOverride 90 (
    lib.concatStringsSep ":" (lib.unique (
      ["${config.xdg.dataHome}/flatpak/exports/share"]
      ++ config.xdg.systemDirs.data
      ++ ["/var/lib/flatpak/exports/share"]
    ))
  );

  targets.genericLinux = {
    enable = true;
    gpu.enable = foundationProfileSchema == 2;
    nixGL = lib.mkIf (foundationProfileSchema == 3) {
      packages = inputs.nixGL.packages;
      defaultWrapper = "mesa";
      vulkan.enable = false;
    };
  };

  services.flatpak = {
    enable = true;
    uninstallUnmanaged = false;
    # Drop runtimes no installed application needs while preserving extra apps.
    uninstallUnused = true;
    update.auto.enable = false;
  };

  xdg.enable = true;
}

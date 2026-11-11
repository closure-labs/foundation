{foundationHost, ...}: {
  # Presence is declarative. Fingerprint enrollment/authentication stays host-owned.
  xdg.configFile."finite/host.json".text = builtins.toJSON foundationHost + "\n";
  home.sessionVariables = {
    FINITE_HOST_SYSTEM = foundationHost.system;
    FINITE_HOST_MODEL = foundationHost.model;
    FINITE_HOST_GPUS = builtins.concatStringsSep "," foundationHost.gpus;
    FINITE_HOST_CAMERA =
      if foundationHost.camera
      then "1"
      else "0";
    FINITE_HOST_FINGERPRINT =
      if foundationHost.fingerprint
      then "1"
      else "0";
  };
}

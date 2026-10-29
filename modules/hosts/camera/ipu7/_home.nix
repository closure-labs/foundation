{ config, lib, pkgs, foundationHost ? null, ... }:
let
  installer = import ./_system-package.nix { inherit pkgs; };
in {
  options.foundation.ipu7.system.enable = lib.mkOption {
    type = lib.types.bool;
    default = foundationHost != null && foundationHost.camera;
    description = "Install the shared IPU7 camera policy through an explained sudo request; unchanged policy skips sudo.";
  };
  config = {
    home.packages = [ installer ];
    # Hardware detection is runtime-only. No capture or legacy repair occurs.
    home.activation.foundationIpu7 = lib.mkIf config.foundation.ipu7.system.enable
      (lib.hm.dag.entryAfter [ "linkGeneration" ] ''
        if [[ -n "''${DRY_RUN:-}" ]]; then
          ${lib.getExe installer} install --dry-run
        else
          ${lib.getExe installer} install
        fi
      '');
  };
}

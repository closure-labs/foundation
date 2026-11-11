{ config, lib, pkgs, ... }:
let
  cfg = config.foundation.dellGrub;
  installer = import ./_package.nix { inherit pkgs; };
in {
  options.foundation.dellGrub.enable = lib.mkOption {
    type = lib.types.bool;
    default = true;
    description = ''
      Enable the graphical GRUB console during Dell model activation on EFI
      OSTree hosts. Explains and requests sudo to manage root-owned boot files.
      Disable before uninstalling with foundation-dell-grub uninstall.
    '';
  };
  config = {
    # Retain the command with the opt-out so removal remains available.
    home.packages = [ installer ];
    home.activation.foundationDellGrub = lib.mkIf cfg.enable (lib.hm.dag.entryAfter [ "linkGeneration" ] ''
      if [[ -n "''${DRY_RUN:-}" ]]; then
        ${lib.getExe installer} install --dry-run
      else
        ${lib.getExe installer} install
      fi
    '');
  };
}

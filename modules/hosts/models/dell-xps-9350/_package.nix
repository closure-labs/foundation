{ pkgs }:
pkgs.writeShellApplication {
  name = "foundation-dell-grub";
  text = ''
    exec ${pkgs.python3}/bin/python3 -I ${./_assets/grub-console.py} "$@"
  '';
}

{ pkgs }:
pkgs.writeShellApplication {
  name = "foundation-camera";
  runtimeInputs = [ pkgs.python3 ];
  text = ''exec python3 ${./_check.py} "$@"'';
}

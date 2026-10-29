{ pkgs }:
let
  source = pkgs.runCommand "foundation-ipu7-system-source" {} ''
    mkdir -p "$out"
    cp ${./_system.py} "$out/_system.py"
    cp ${./_policy.conf} "$out/_policy.conf"
  '';
in pkgs.writeShellApplication {
  name = "foundation-ipu7-system";
  text = ''exec ${pkgs.python3}/bin/python3 -I ${source}/_system.py "$@"'';
}

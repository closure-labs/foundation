{ lib, pkgs, ... }:
let
  source = pkgs.runCommand "foundation-flatpak-observation-source" { } ''
    mkdir -p "$out"
    cp ${../../../scripts/service_observation.py} "$out/service_observation.py"
    cp ${../../../scripts/foundation_observations.py} "$out/foundation_observations.py"
  '';
  observe =
    original:
    pkgs.writeShellScript "foundation-observe-flatpak" ''
      exec ${pkgs.python3}/bin/python3 ${source}/service_observation.py ${lib.escapeShellArg (toString original)}
    '';
in
{
  # Transform only the pinned provider's single executable, after definitions
  # merge. Keep Type, restart policy, activation DAG and synchronous startup.
  options.systemd.user.services = lib.mkOption {
    apply = lib.mapAttrs (
      name: unit:
      let
        commands = lib.toList (unit.Service.ExecStart or [ ]);
        original = if builtins.length commands == 1 then builtins.head commands else "";
      in
      if
        name == "flatpak-managed-install"
        && builtins.length commands == 1
        && lib.hasPrefix "/nix/store/" (toString original)
        && lib.hasSuffix "-flatpak-managed-install" (toString original)
      then
        unit
        // {
          Service = unit.Service // {
            ExecStart = [ (observe original) ];
            EnvironmentFile = (lib.toList (unit.Service.EnvironmentFile or [ ])) ++ [
              "-%t/foundation-observation.env"
            ];
          };
        }
      else
        unit
    );
  };
}

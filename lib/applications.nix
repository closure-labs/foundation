{
  pkgs,
  source,
  sourceInfo ? {},
}: let
  metadata = pkgs.writeText "foundation-source.json" (builtins.toJSON sourceInfo);
  command = name: operation:
    pkgs.writeShellApplication {
      inherit name;
      runtimeInputs = with pkgs; [python3 coreutils git jq yq-go util-linux libnotify zenity];
      text = ''
        export FINITE_FOUNDATION_SOURCE=${source}
        export FINITE_FOUNDATION_METADATA=${metadata}
        export FINITE_FOUNDATION_CATALOG=${homeCatalog}
        exec python3 ${source}/scripts/home.py ${operation} "$@"
      '';
    };
  homeCatalog = pkgs.writeText "home-profile-catalog.json" (builtins.toJSON
    (import ./home-catalog.nix {
      domainCatalog = import ./catalog.nix;
      inherit (pkgs) lib;
      version = pkgs.lib.removeSuffix "\n" (builtins.readFile ../VERSION);
    }));
in {
  profileCatalog = homeCatalog;
  homeProfile = import ./profile.nix {
    inherit pkgs;
    catalog = homeCatalog;
  };
  homeInit = command "finite-home-init" "init";
  homeBootstrap = command "finite-home-bootstrap" "init";
  homeApply = command "finite-home-apply" "apply";
  homeUpdate = command "finite-home-update" "update";
  homeMigrate = command "finite-home-migrate" "migrate";
  appStatus = command "finite-app-status" "status";
}

{
  pkgs,
  source,
  sourceInfo ? {},
}: let
  helperSource = import ../../../lib/helper-source.nix source;
  metadata = pkgs.writeText "foundation-source.json" (builtins.toJSON sourceInfo);
  command = name: operation:
    pkgs.writeShellApplication {
      inherit name;
      runtimeInputs = with pkgs; [python3 coreutils git jq yq-go util-linux libnotify zenity];
      text = ''
        export FINITE_FOUNDATION_SOURCE=${helperSource}
        export FINITE_FOUNDATION_METADATA=${metadata}
        export FINITE_FOUNDATION_CATALOG=${homeCatalog}
        exec python3 ${helperSource}/scripts/home.py ${operation} "$@"
      '';
    };
  homeCatalog = pkgs.writeText "home-profile-catalog.json" (builtins.toJSON
    (import ../../../lib/profile-catalog.nix {
      domainCatalog = import ../../../lib/catalog.nix;
      inherit (pkgs) lib;
      version = pkgs.lib.removeSuffix "\n" (builtins.readFile ../../../VERSION);
    }));
in rec {
  camera = import ../../hosts/camera/ipu7/_package.nix { inherit pkgs; };
  profileCatalog = homeCatalog;
  homeProfile = import ../../../lib/profile.nix {
    inherit pkgs;
    source = helperSource;
  };
  homeInit = command "foundation-home-init" "init";
  homeBootstrap = command "foundation-home-bootstrap" "init";
  homeApply = command "foundation-home-apply" "apply";
  homeUpdate = command "foundation-home-update" "update";
  homeMigrate = command "foundation-home-migrate" "migrate";
  configure = pkgs.writeShellApplication {
    name = "foundation-configure";
    runtimeInputs = with pkgs; [coreutils jq zenity homeApply];
    text = builtins.readFile ./_assets/foundation-configure;
  };
  foundation = pkgs.writeShellApplication {
    name = "foundation";
    text = ''
      usage() {
        echo 'Usage: foundation home <check|apply|update|init|profile|configure|migrate|status|camera> [arguments]'
      }
      case "''${1:-}" in
        -h|--help) usage; exit 0 ;;
        home) shift ;;
        *) usage >&2; exit 2 ;;
      esac
      case "''${1:-}" in
        -h|--help) usage; exit 0 ;;
        camera) shift; exec ${camera}/bin/foundation-camera "$@" ;;
        check) shift; ${camera}/bin/foundation-camera || echo "Camera check needs attention; continuing configuration build." >&2; exec ${homeApply}/bin/foundation-home-apply --check "$@" ;;
        apply) shift; exec ${homeApply}/bin/foundation-home-apply "$@" ;;
        update) shift; exec ${homeUpdate}/bin/foundation-home-update "$@" ;;
        init) shift; exec ${homeInit}/bin/foundation-home-init "$@" ;;
        profile) shift; exec ${homeProfile}/bin/foundation-home-profile "$@" ;;
        configure) shift; exec ${configure}/bin/foundation-configure "$@" ;;
        migrate) shift; exec ${homeMigrate}/bin/foundation-home-migrate "$@" ;;
        status) shift; exec ${appStatus}/bin/foundation-app-status "$@" ;;
        *) usage >&2; exit 2 ;;
      esac
    '';
  };
  appStatus = command "foundation-app-status" "status";
}

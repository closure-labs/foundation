{ config, lib, ... }: let
  explicit = config.foundation.configRoot;
  root = if explicit != null then explicit else "${config.xdg.configHome}/home-manager";
  reference = { type = "path"; path = root; };
in {
  options.foundation.configRoot = lib.mkOption {
    type = lib.types.nullOr (lib.types.addCheck lib.types.str (path: lib.hasPrefix "/" path));
    default = null;
    description = "Optional absolute runtime path shared by NH and Foundation helpers; null uses the XDG config home.";
  };
  config = {
    programs.nh.homeFlake = lib.mkDefault (builtins.deepSeq reference (builtins.flakeRefToString reference));
    # Do not export the default: the CLI must still honor runtime XDG overrides.
    home.sessionVariables = lib.mkIf (explicit != null) {
      FINITE_HOME_FLAKE_PATH = explicit;
    };
  };
}

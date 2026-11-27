# Evaluate all draft Nix provider identities against the actual locked inputs.
# No GUI package is built or launched by this check.
{foundation}: let
  inherit (foundation.lib.inputs.nixpkgs) lib;
  system = "x86_64-linux";
  sources = import ../modules/providers/nixpkgs/_package-sets.nix {
    inputs = foundation.lib.inputs;
    inherit system;
  };
  applications = lib.filterAttrs (_: app: app.provider == "nix") foundation.lib.profileDrafts.contract.applications;
in
  lib.mapAttrs (_: app: let
    source =
      if app.input == "devenv"
      then foundation.lib.inputs.devenv.packages.${system}
      else if app.input == "ai"
      then foundation.lib.inputs.${app.pin}.packages.${system}
      else sources.${app.pin or app.input};
    path = lib.splitString "." app.attribute;
    package = lib.attrByPath path null source;
  in {
    inherit (app) input attribute;
    available = lib.isDerivation package;
  })
  applications

# Evaluate all draft Nix provider identities against the actual locked inputs.
# No GUI package is built or launched by this check.
{foundation}: let
  inherit (foundation.inputs.nixpkgs) lib;
  system = "x86_64-linux";
  sources = lib.genAttrs ["nixpkgs" "nixpkgs-weekly" "nixpkgs-unstable"] (name:
    import foundation.inputs.${name} {
      inherit system;
      config.allowUnfree = true;
    });
  applications = lib.filterAttrs (_: app: app.provider == "nix") foundation.lib.profileDrafts.contract.applications;
in
  lib.mapAttrs (_: app: let
    source =
      if app.input == "devenv"
      then foundation.inputs.devenv.packages.${system}
      else sources.${app.input};
    path = lib.splitString "." app.attribute;
    package = lib.attrByPath path null source;
  in {
    inherit (app) input attribute;
    available = lib.isDerivation package;
  })
  applications

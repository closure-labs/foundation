{ lib, config, ... }:
let
  loader = import ./_loader.nix { };
in
{
  options.foundation.features = lib.mkOption {
    type = lib.types.attrsOf lib.types.raw;
    default = { };
    description = "Discovered feature descriptors; registration never activates a home.";
  };

}

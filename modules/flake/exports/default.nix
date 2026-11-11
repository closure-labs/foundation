{ inputs, config, ... }:
let
  outputs = import ./_outputs.nix inputs;
in
{
  flake = outputs // {
    lib = outputs.lib // {
      discoveredFeatures = builtins.attrNames config.foundation.features;
    };
  };
}

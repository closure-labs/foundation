{ lib, ... }: {
  options.foundation.featureIds = lib.mkOption {
    type = lib.types.listOf lib.types.str;
    default = [];
    internal = true;
    description = "Feature IDs actually imported by Den.";
  };
}

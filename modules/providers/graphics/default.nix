{ ... }: {
  foundation.features."providers/graphics" = import ./_feature.nix;
  flake-file.inputs.nixGL = {
    url = "github:nix-community/nixGL";
    inputs.nixpkgs.follows = "nixpkgs";
  };
}

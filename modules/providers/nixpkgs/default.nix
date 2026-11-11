{ ... }: {
  foundation.features."providers/nixpkgs" = import ./_feature.nix;
  flake-file.inputs.nixpkgs.url = "https://flakehub.com/f/DeterminateSystems/nixpkgs-26.05-chilled/0.1";
}

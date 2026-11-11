{ ... }: {
  foundation.features."providers/nixpkgs-weekly" = import ./_feature.nix;
  flake-file.inputs.nixpkgs-weekly.url = "https://flakehub.com/f/DeterminateSystems/nixpkgs-weekly/0.1";
}

{ ... }: {
  foundation.features."providers/nixpkgs-unstable" = import ./_feature.nix;
  flake-file.inputs.nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
}

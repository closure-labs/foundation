{ ... }: {
  foundation.features."providers/nixpkgs-unstable" = import ./_feature.nix;
}

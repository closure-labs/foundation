{ ... }: {
  foundation.features."providers/nixpkgs" = import ./_feature.nix;
}

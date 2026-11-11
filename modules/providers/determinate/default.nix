{ ... }: {
  foundation.features."providers/determinate" = import ./_feature.nix;
  flake-file.inputs.determinate.url = "https://flakehub.com/f/DeterminateSystems/determinate/3";
}

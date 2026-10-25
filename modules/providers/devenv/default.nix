{ ... }: {
  foundation.features."providers/devenv" = import ./_feature.nix;
  flake-file.inputs.devenv.url = "github:cachix/devenv/v2.2.2";
}

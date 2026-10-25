{ ... }: {
  foundation.features."providers/flatpak" = import ./_feature.nix;
  flake-file.inputs.nix-flatpak.url = "github:gmodena/nix-flatpak";
}

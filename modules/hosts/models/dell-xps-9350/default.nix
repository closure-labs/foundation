{ inputs, ... }:
let
  system = "x86_64-linux";
  package = import ./_package.nix { pkgs = inputs.nixpkgs.legacyPackages.${system}; };
in {
  foundation.features."hosts/models/dell-xps-9350" = import ./_feature.nix;
  flake.packages.${system}.dell-grub = package;
  flake.apps.${system}.dell-grub = {
    type = "app";
    program = "${package}/bin/foundation-dell-grub";
  };
}

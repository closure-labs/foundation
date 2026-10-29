{ inputs, ... }:
let
  system = "x86_64-linux";
  package = import ./_system-package.nix { pkgs = inputs.nixpkgs.legacyPackages.${system}; };
in {
  foundation.features."hosts/camera/ipu7" = import ./_feature.nix;
  flake.packages.${system}.ipu7-system = package;
  flake.apps.${system}.ipu7-system = {
    type = "app";
    program = "${package}/bin/foundation-ipu7-system";
  };
}

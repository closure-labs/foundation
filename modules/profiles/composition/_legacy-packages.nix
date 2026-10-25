{ inputs, pkgs }: let
  features = (import ../../flake/features/_loader.nix {}).features;
  sources = {
    nixpkgs = pkgs;
    nixpkgs-weekly = inputs.nixpkgs-weekly.legacyPackages.${pkgs.stdenv.hostPlatform.system};
    nixpkgs-unstable = inputs.nixpkgs-unstable.legacyPackages.${pkgs.stdenv.hostPlatform.system};
    devenv = inputs.devenv.packages.${pkgs.stdenv.hostPlatform.system};
  };
in name: let app = features."apps/${name}".metadata.legacyApplication; in
  if (app.recipe or null) == "finite-ghostty" then import ../../apps/ghostty/_package.nix { inherit pkgs; }
  else builtins.foldl' (set: attr: set.${attr}) sources.${app.input}
    (builtins.filter builtins.isString (builtins.split "\\." app.attribute))

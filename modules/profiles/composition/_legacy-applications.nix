{ id, base ? false }: { inputs, lib, pkgs, foundationProfileSchema ? 2, ... }: let
  loader = import ../../flake/features/_loader.nix {};
  inherit (loader) features;
  names = map (dep: builtins.substring 5 (builtins.stringLength dep) dep)
    (builtins.filter (dep: builtins.substring 0 5 dep == "apps/") (loader.dependencies 2 id));
  app = name: features."apps/${name}".metadata.legacyApplication;
  nixIds = builtins.filter (name: (app name).provider == "nix" && name != "firefox") names;
  ordered = if base then builtins.sort (a: b:
    features."apps/${a}".metadata.legacyBaseOrder < features."apps/${b}".metadata.legacyBaseOrder) nixIds else nixIds;
  packageFor = import ./_legacy-packages.nix { inherit inputs pkgs; };
  packages = lib.optionals (foundationProfileSchema == 2) (map packageFor ordered);
  flatpaks = lib.optionals (foundationProfileSchema == 2)
    (map (name: (app name).id) (builtins.filter (name: (app name).provider == "flatpak") names));
in {
  home.packages = if base then lib.mkOrder 680 packages else packages;
  services.flatpak.packages = if base then lib.mkAfter flatpaks else flatpaks;
}

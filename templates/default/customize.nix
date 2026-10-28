{
  foundationPackageSets,
  pkgs,
  ...
}: let
  weekly = foundationPackageSets.nixpkgs-weekly;
in {
  # Add personal packages and settings here; lists merge with the base modules.
  home.packages =
    (with pkgs; [
      # jq
    ])
    ++ (with weekly; [
      # example
    ]);

  services.flatpak.packages = [
    #   "org.gimp.GIMP"
  ];
}

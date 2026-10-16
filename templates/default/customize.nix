{
  inputs,
  pkgs,
  ...
}: let
  weekly = inputs.nixpkgs-weekly.legacyPackages.${pkgs.stdenv.hostPlatform.system};
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

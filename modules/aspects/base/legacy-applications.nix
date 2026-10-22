{
  inputs,
  lib,
  pkgs,
  foundationProfileSchema ? 2,
  ...
}: let
  system = pkgs.stdenv.hostPlatform.system;
  weekly = inputs.nixpkgs-weekly.legacyPackages.${system};
in {
  # Schema 3 resolves application membership in profile-composition.nix.
  home.packages = lib.optionals (foundationProfileSchema == 2) (
    (with pkgs; [
      marp-cli
      neovim
    ])
    ++ [
      weekly.bitwarden-desktop
      weekly.element-desktop
      weekly.libreoffice
      weekly.nextcloud-client
      pkgs.thunderbird
      pkgs.vlc
      weekly.bitwarden-cli
    ]
  );

  # Retain the base applications after role-specific Flatpak declarations.
  services.flatpak.packages = lib.mkAfter (lib.optionals (foundationProfileSchema == 2) [
    "app.drey.Damask"
    "be.alexandervanhee.gradia"
    "com.github.PintaProject.Pinta"
    "com.github.tchx84.Flatseal"
    "com.mattjakeman.ExtensionManager"
    "com.ranfdev.DistroShelf"
    "hu.irl.cameractrls"
    "io.github.flattool.Ignition"
    "io.github.flattool.Warehouse"
    "io.github.pleromix.IceBox"
    "io.github.zaedus.spider"
    "io.gitlab.adhami3310.Impression"
    "io.missioncenter.MissionCenter"
    "it.mijorus.gearlever"
    "it.mijorus.smile"
    "net.cozic.joplin_desktop"
    "org.chromium.Chromium"
    "page.tesk.Refine"
  ]);
}

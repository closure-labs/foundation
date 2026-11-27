{
  lib,
  pkgs,
  ...
}:
let
  waylandEnvironment = lib.mapAttrs (_: lib.mkDefault) {
    NIXOS_OZONE_WL = "1";
    MOZ_ENABLE_WAYLAND = "1";
    QT_QPA_PLATFORM = "wayland;xcb";
    GDK_BACKEND = "wayland,x11";
  };
  source = pkgs.runCommand "foundation-bluefin-preparation-source" { } ''
    mkdir -p "$out"
    cp ${./_prepare.py} "$out/prepare.py"
    cp ${../../../../scripts/foundation_observations.py} "$out/foundation_observations.py"
  '';
  prepare = pkgs.writeShellApplication {
    name = "foundation-prepare";
    runtimeInputs = [ pkgs.python3 ];
    text = ''exec python3 ${source}/prepare.py "$@"'';
  };
in
{
  home.sessionVariables = waylandEnvironment;
  systemd.user.sessionVariables = waylandEnvironment;

  # GNOME's portal rejects inherited GDK_BACKEND fallback lists and then
  # exports Settings alone, breaking Save As dialogs and screen sharing.
  # Scope the correction to the host portal; applications keep their own env.
  xdg.configFile."systemd/user/xdg-desktop-portal-gnome.service.d/20-display-backend.conf".text = lib.mkDefault ''
    [Service]
    UnsetEnvironment=GDK_BACKEND
  '';

  # Keep the existing integration with Bluefin's stock Fzf binary.
  # HM's pinned Fzf module cannot be enabled without installing its package,
  # so keep the explicit Finite shell integration as declarative configuration.
  programs.zsh.initContent = lib.mkOrder 910 ''
    if [[ -x /usr/bin/fzf ]]; then
      source <(/usr/bin/fzf --zsh)
    elif [[ -x /home/linuxbrew/.linuxbrew/bin/fzf ]]; then
      source <(/home/linuxbrew/.linuxbrew/bin/fzf --zsh)
    fi
  '';
  # Optional Bluefin CLI bundles remain user opt-ins, including bbrew/ugrep/uutils.
  # Do not add second Nix copies here or filter explicit personal packages.
  # Pinned Home Manager 24f2190 exposes this generation builder extension.
  # The generic initializer executes this fixed generation-relative entry only.
  home.extraBuilderCommands = ''
    ln -s ${prepare}/bin/foundation-prepare "$out/foundation-prepare"
  '';
}

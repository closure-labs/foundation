{
  lib,
  pkgs,
  ...
}:
let
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

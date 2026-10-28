args@{
  inputs,
  lib,
  pkgs,
  ...
}:
let
  packageSets = args.foundationPackageSets or (import ../../../providers/nixpkgs/_package-sets.nix {
    inherit inputs;
    system = pkgs.stdenv.hostPlatform.system;
  });
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
  # The pinned image owns Fzf and Starship via preinstall.d/system-cli.Brewfile.
  # HM's pinned Fzf module cannot be enabled without installing its package,
  # so keep the explicit Finite shell integration as declarative configuration.
  programs.zsh.initContent = lib.mkOrder 910 ''
    if [[ -x /home/linuxbrew/.linuxbrew/bin/fzf ]]; then
      source <(/home/linuxbrew/.linuxbrew/bin/fzf --zsh)
    fi
  '';
  # Historical copied-policy entries absent from both upstream stock bundles.
  # These are Finite additions; no Brew formula/tap declaration is retained.
  home.packages = [
    (pkgs.bbrew or packageSets.nixpkgs-unstable.bbrew)
    pkgs.ugrep
    pkgs.uutils-coreutils
  ];
  # Pinned Home Manager 24f2190 exposes this generation builder extension.
  # The generic initializer executes this fixed generation-relative entry only.
  home.extraBuilderCommands = ''
    ln -s ${prepare}/bin/foundation-prepare "$out/foundation-prepare"
  '';
}

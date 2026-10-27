{
  config,
  finiteHomeAssets,
  lib,
  pkgs,
  foundationProfileSchema ? 2,
  ...
}:
let
  ghostty = import ../../apps/ghostty/_package.nix { inherit pkgs; };
in
{
  imports = [
    (import ../../profiles/composition/_legacy-applications.nix { id = "capabilities/devops"; })
  ];

  # Terminal multiplexers inherit SHELL even when Ghostty starts Zsh directly.
  home.sessionVariables.SHELL = lib.mkDefault "${config.programs.zsh.package}/bin/zsh";

  programs.zsh = {
    enable = true;
    dotDir = "${config.xdg.configHome}/zsh";
    envExtra = builtins.readFile (finiteHomeAssets.devops + "/zsh/.zshenv");
    autosuggestion.enable = true;
    enableCompletion = true;
    completionInit = ''
      mkdir -p "${config.xdg.cacheHome}/zsh"
      autoload -Uz compinit
      compinit -d "${config.xdg.cacheHome}/zsh/zcompdump"
    '';
    history = {
      path = "${config.xdg.stateHome}/zsh/history";
      size = 100000;
      save = 100000;
      append = true;
      expireDuplicatesFirst = true;
      findNoDups = true;
    };
    historySubstringSearch.enable = true;
    plugins = [
      {
        name = "zsh-vi-mode";
        file = "share/zsh-vi-mode/zsh-vi-mode.plugin.zsh";
        src = pkgs.zsh-vi-mode;
      }
    ];
    syntaxHighlighting.enable = true;
    # Bluefin retains stock binary precedence. Home Manager owns Finite Zsh configuration.
    initContent = lib.mkMerge [
      (lib.mkBefore ''
        # Refresh inherited login-session values in every interactive shell.
        export SHELL="${config.programs.zsh.package}/bin/zsh"
      '')
      (builtins.readFile (finiteHomeAssets.devops + "/zsh/.zshrc"))
    ];
  };

  xdg.configFile = {
    "ghostty/config.ghostty".text =
      builtins.replaceStrings
        [ "command = /usr/bin/zsh" ]
        [ "command = ${config.programs.zsh.package}/bin/zsh" ]
        (builtins.readFile (finiteHomeAssets.devops + "/ghostty/config.ghostty"));
    "zsh/aliases.zsh".source = finiteHomeAssets.devops + "/zsh/aliases.zsh";
    "zsh/bindings.zsh".source = finiteHomeAssets.devops + "/zsh/bindings.zsh";
    "zsh/fzf.zsh".source = finiteHomeAssets.devops + "/zsh/fzf.zsh";
    "zsh/prompt.zsh".source = finiteHomeAssets.devops + "/zsh/prompt.zsh";
    "zsh/starship.toml".source = finiteHomeAssets.devops + "/zsh/starship.toml";
  };
}

{...}: {
  programs = {
    fzf.enable = true;
    git.enable = true;
    # nh can activate homes without installing the standalone CLI.
    home-manager.enable = true;
    nh.enable = true;
    zsh.enable = true;
  };
}

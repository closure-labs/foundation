{inputs, lib, ...}: {
  # Keep the shared aspect entry point small; application selection stays in
  # profile composition and the explicit schema-2 declarations.

  imports = [./_membership.nix];
  home = {
    username = lib.mkDefault "finite";
    homeDirectory = lib.mkDefault "/var/home/finite";
    stateVersion = "26.05";
  };

  nix.package = null;

  # Keep this ordered startup hook at the base entry point so private imports
  # do not reorder it relative to role and consumer mkBefore initialization.
  programs.zsh.initContent = lib.mkBefore ''
    # Apply the shared CLI provider policy after Bluefin's global rc.
    path=(
      /home/linuxbrew/.linuxbrew/opt/uutils-coreutils/libexec/uubin
      /home/linuxbrew/.linuxbrew/bin
      /home/linuxbrew/.linuxbrew/sbin
      $path
    )
  '';
}

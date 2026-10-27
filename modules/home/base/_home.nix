{ inputs, lib, ... }: {
  # Keep the shared aspect entry point small; application selection stays in
  # schema-3 profile composition.

  imports = [ ./_membership.nix ];
  home = {
    username = lib.mkDefault "finite";
    homeDirectory = lib.mkDefault "/var/home/finite";
    stateVersion = "26.05";
  };

  nix.package = null;

}

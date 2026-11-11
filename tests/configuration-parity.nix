{ foundation, profile }: let
  home = foundation.lib.mkHomeConfiguration { inherit profile; modules = [ (foundation.outPath + "/customize.nix") (foundation.outPath + "/modules/local.nix") ]; };
  c = home.config;
in {
  packages = map (p: { name = p.name or ""; path = p.outPath; priority = p.meta.priority or 5; }) c.home.packages;
  inherit (c.home) stateVersion sessionVariables;
  zsh = c.programs.zsh.initContent;
  flatpaks = c.services.flatpak.packages;
  activation = c.home.activation;
  services = c.systemd.user.services;
  files = builtins.mapAttrs (_: v: { inherit (v) text; source = toString v.source; }) c.xdg.configFile;
}

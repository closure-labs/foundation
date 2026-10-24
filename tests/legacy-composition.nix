{foundation, profile}: let
  home = foundation.lib.mkHomeConfiguration {
    inherit profile;
    modules = [
      (foundation.outPath + "/customize.nix")
      (foundation.outPath + "/modules/local.nix")
    ];
  };
in {
  drv = home.activationPackage.drvPath;
  homeManagerCliInstalled = builtins.elem home.config.programs.home-manager.package.outPath (map (p: p.outPath) home.config.home.packages);
}

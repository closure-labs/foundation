{ foundation, profile }:
let
  home = foundation.lib.mkHomeConfiguration {
    inherit profile;
    modules = [
      (foundation.outPath + "/customize.nix")
      (foundation.outPath + "/modules/local.nix")
    ];
  };
in
{
  drv = home.activationPackage.drvPath;
  bluefinAspectSelected = builtins.elem "hosts/os/bluefin" home.config.foundation.featureIds;
  preparationAttached = home.pkgs.lib.hasInfix "foundation-prepare" home.config.home.extraBuilderCommands;
  stockFzfNotDuplicated =
    !(builtins.elem home.pkgs.fzf.outPath (map (p: p.outPath) home.config.home.packages));
  unmanagedFlatpaksPreserved = home.config.services.flatpak.uninstallUnmanaged == false;
  flatpakServiceWrapped =
    let
      commands = home.config.systemd.user.services.flatpak-managed-install.Service.ExecStart;
    in
    builtins.length commands == 1
    && home.pkgs.lib.hasInfix "foundation-observe-flatpak" (toString (builtins.head commands));
  homeManagerCliInstalled = builtins.elem home.config.programs.home-manager.package.outPath (
    map (p: p.outPath) home.config.home.packages
  );
}

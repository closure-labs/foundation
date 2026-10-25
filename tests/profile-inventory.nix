# Import the actual legacy modules with symbolic packages. No daemon/downloads.
let
  catalog = import ../lib/catalog.nix;
  draft = import ../lib/profile-drafts {inherit catalog;};
  applications = draft.contract.legacyApplications;
  forInput = input:
    builtins.listToAttrs (map (name: {
        name = applications.${name}.attribute;
        value = applications.${name}.declaration;
      }) (builtins.filter (name: applications.${name}.provider == "nix" && applications.${name}.input == input)
        (builtins.attrNames applications)));
  pkgs =
    forInput "nixpkgs"
    // {
      stdenv.hostPlatform.system = "fixture";
      writeShellApplication = _: "infrastructure:brew-provider-policy";
      symlinkJoin = _: applications.ghostty.declaration;
    };
  weekly = forInput "nixpkgs-weekly" // {firefox.override = _: applications.firefox.declaration;};
  args = {
    inherit pkgs;
    config = {};
    lib.optionals = condition: values:
      if condition
      then values
      else [];
    lib.mkOrder = _: values: values;
    lib.mkAfter = values: values;
    finiteHomeAssets.devops = ../modules/capabilities/devops/_assets/rootfs/usr/share/finite;
    inputs = {
      determinate.homeManagerModules.default = {};
      nix-flatpak.homeManagerModules.nix-flatpak = {};
      nixpkgs-weekly.legacyPackages.fixture = weekly;
      devenv.packages.fixture.devenv = applications.devenv.declaration;
    };
  };
  loader = import ../modules/flake/features/_loader.nix {};
  moduleDeclarations = module:
    builtins.filter (value: value != "infrastructure:brew-provider-policy") (module.home.packages or [])
    ++ map (id: "flatpak:flathub:${id}") (module.services.flatpak.packages or [])
    ++ map (name: "desktop-entry:${name}") (builtins.attrNames (module.xdg.desktopEntries or {}))
    ++ (
      if module.programs.firefox.enable or false
      then [module.programs.firefox.package]
      else []
    )
    # Follow the actual private module imports instead of assuming every base
    # declaration is defined directly in its aspect entry point.
    ++ builtins.concatLists (map (entry:
      moduleDeclarations (
        if builtins.isAttrs entry then entry else if builtins.isFunction entry then entry args else import entry args
      )) (module.imports or []));
  aspectDeclarations = id: builtins.concatLists (map (name: let
    descriptor = loader.features.${name};
    module = if descriptor ? configuration then descriptor.configuration 2 else {};
  in moduleDeclarations (if builtins.isFunction module then module args else module)) (loader.closure 2 [id]));
  sorted = values: builtins.sort builtins.lessThan values;
in {
  common = sorted (aspectDeclarations "home/base");
  roles = builtins.listToAttrs (map (name: { inherit name; value = sorted (aspectDeclarations "roles/${name}"); }) catalog.roleNames);
}

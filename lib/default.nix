{inputs}: let
  inherit (inputs.nixpkgs) lib;
  version = lib.removeSuffix "\n" (builtins.readFile ../VERSION);
  catalog = import ./catalog.nix;
  normalizeProfile = import ./normalize-profile.nix {inherit catalog;};
  sourceInfo = {
    inherit version;
    compatibility = 1;
    schema = 1;
    rev = inputs.self.rev or null;
    narHash = inputs.self.narHash or null;
    lastModified = inputs.self.lastModified or 0;
  };
  homeCatalog = import ./home-catalog.nix {
    domainCatalog = catalog;
    inherit lib version;
  };
  mkApplications = {
    pkgs,
    releaseInfo ? sourceInfo,
  }:
    import ./applications.nix {
      inherit pkgs;
      source = ../.;
      sourceInfo = releaseInfo;
    };
in {
  inherit catalog homeCatalog sourceInfo mkApplications normalizeProfile;
  inherit (homeCatalog) profileCapabilities;
  profileDrafts = import ./profile-drafts {inherit catalog;};
  mkHomeCatalog = {domainCatalog ? catalog}: import ./home-catalog.nix {inherit domainCatalog lib version;};
  compatibility = 1;
  mkHomeConfiguration = {
    profile,
    modules ? [],
    extraInputs ? {},
  }: let
    normalized = normalizeProfile profile;
    evaluated = lib.evalModules {
      specialArgs = {
        inputs = inputs // extraInputs;
        foundationProfile = normalized;
        foundationModules = modules;
      };
      modules = [inputs.den.flakeModule ../modules/finite.nix];
    };
  in
    evaluated.config.flake.homeConfigurations.${normalized.identity.username};
  mkConsumerTemplate = {
    pkgs,
    releaseInfo ? sourceInfo,
  }: let
    metadata = pkgs.writeText "foundation-source.json" (builtins.toJSON releaseInfo);
  in
    pkgs.runCommand "foundation-consumer-${version}" {nativeBuildInputs = [pkgs.python3];} ''
      python3 ${../scripts/home.py} template --source ${../.} --metadata ${metadata} --output "$out"
    '';
}

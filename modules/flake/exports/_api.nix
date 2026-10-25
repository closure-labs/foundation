{inputs}: let
  inherit (inputs.nixpkgs) lib;
  version = lib.removeSuffix "\n" (builtins.readFile ../../../VERSION);
  catalog = import ../../../lib/catalog.nix;
  normalizeProfile = import ../../../lib/normalize-profile.nix {inherit catalog;};
  profileComposition = import ../../../lib/profile-drafts {inherit catalog;};
  sourceInfo = {
    inherit version;
    compatibility = 1;
    schema = 1;
    rev = inputs.self.rev or null;
    narHash = inputs.self.narHash or null;
    lastModified = inputs.self.lastModified or 0;
  };
  homeCatalogForSchema = schema:
    import ../../../lib/profile-catalog.nix {
      domainCatalog = catalog;
      inherit lib version schema;
    };
  homeCatalog = homeCatalogForSchema 3;
  mkApplications = {
    pkgs,
    releaseInfo ? sourceInfo,
  }:
    import ../../../lib/applications.nix {
      inherit pkgs;
      source = ../../..;
      sourceInfo = releaseInfo;
    };
in {
  ciGraph = import ../../ci/_graph.nix;
  inherit catalog homeCatalog homeCatalogForSchema sourceInfo mkApplications normalizeProfile;
  hosts = import ../../../lib/hosts.nix;
  inherit (homeCatalog) profileCapabilities;
  profileDrafts = profileComposition;
  resolveProfile = profileComposition.resolve;
  profileChanges = {
    schema = 1;
    preview = import ../../../lib/profile-changes.nix {inherit catalog;};
  };
  mkHomeCatalog = {
    domainCatalog ? catalog,
    schema ? 3,
  }:
    import ../../../lib/profile-catalog.nix {inherit domainCatalog lib version schema;};
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
      modules = [inputs.den.flakeModule inputs.den.flakeOutputs.homeConfigurations ../../home/construction/_module.nix];
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
      python3 ${../../../scripts/home.py} template --source ${../../..} --metadata ${metadata} --output "$out"
    '';
}

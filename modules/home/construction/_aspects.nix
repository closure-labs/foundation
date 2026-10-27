{ den, lib, foundationProfile ? {schema = 3;}, ... }: let
  loader = import ../../flake/features/_loader.nix {};
  schema = foundationProfile.schema or 3;
  aspects = builtins.mapAttrs (id: descriptor: {
    includes = map (dependency: den.aspects.foundation.${dependency}) (loader.dependencies schema id);
    homeManager.imports = [
      ../base/_membership.nix
      (if descriptor ? configuration then descriptor.configuration schema else {})
      { foundation.featureIds = [id]; }
    ];
  }) loader.features;
  alias = id: den.aspects.foundation.${id};
  named = prefix: names: lib.genAttrs names (name: alias "${prefix}/${name}");
in {
  den.aspects.foundation = aspects;
  den.aspects.features = {
    base = alias "home/base";
    capabilities.devops = alias "capabilities/devops";
    profile-composition = alias "profiles/composition";
    host = alias "hosts/identity";
    roles = named "roles" (import ../../../lib/catalog.nix).roleNames;
    machines = named "hosts/machines" ["generic" "laptop" "desktop"];
    hardware = {
      cpu = named "hosts/cpu" ["generic" "intel" "amd"];
      gpu = named "hosts/gpu" ["intel-integrated" "intel-discrete" "amd-integrated" "amd-discrete"];
      models = named "hosts/models" ["generic" "dell-xps-9350"];
      generic-x86_64.homeManager.imports = [
      ../base/_membership.nix../../hosts/models/generic/_home.nix];
      dell-xps-9350-intel = alias "hosts/models/dell-xps-9350";
    };
  };
}

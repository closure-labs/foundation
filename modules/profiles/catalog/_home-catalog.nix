{
  domainCatalog,
  lib,
  version,
}: let
  inherit (domainCatalog) packageNames roleNames;
  classificationsByName = builtins.listToAttrs (
    map (entry: {
      inherit (entry) name;
      value = entry;
    }) (domainCatalog.classifications or [])
  );
  classificationFor = role: let
    classification = role.classification or null;
  in
    if classification == null || (builtins.isString classification && builtins.hasAttr classification classificationsByName)
    then classification
    else throw "Unknown Foundation classification ${builtins.toJSON classification} for role ${role.name}";
  orderedRoleNames =
    builtins.sort
    (a: b: domainCatalog.rolesByName.${a}.order < domainCatalog.rolesByName.${b}.order)
    roleNames;
in {
  schema = 3;
  profileCapabilities = builtins.fromJSON (builtins.readFile ../../../lib/profile-capabilities.json);
  inherit version;
  classifications = lib.mapAttrs (
    name: classification: {
      inherit (classification) name label order;
      roles = builtins.filter (role: classificationFor domainCatalog.rolesByName.${role} == name) orderedRoleNames;
    }
  ) classificationsByName;
  foundations =
    lib.mapAttrs (
      _: foundation: {
        inherit (foundation) name template;
        profiles = lib.mapAttrs (_: profile: profile.name) (foundation.profiles or {});
        hardware = domainCatalog.homeHardwareNames;
        packages = packageNames;
        roles = roleNames;
      }
    )
    domainCatalog.foundationsByName;
  hardware = lib.genAttrs domainCatalog.homeHardwareNames (
    name: {
      inherit (domainCatalog.hardwareByName.${name}) imageHardware label name;
    }
  );
  roles =
    lib.mapAttrs (
      _: role: {
        inherit (role) label name order;
        classification = classificationFor role;
        foundations = domainCatalog.foundationNames;
      }
    )
    domainCatalog.rolesByName;
  packages =
    lib.mapAttrs (
      _: package: {
        inherit (package) description label name order;
        foundations = domainCatalog.foundationNames;
      }
    )
    domainCatalog.packagesByName;
  compatibility =
    lib.mapAttrs (_: _foundation: {
      hardware = domainCatalog.homeHardwareNames;
      packages = packageNames;
      roles = roleNames;
    })
    domainCatalog.foundationsByName;
}

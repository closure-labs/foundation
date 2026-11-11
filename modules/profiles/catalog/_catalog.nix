let
  features = (import ../../flake/features/_loader.nix {}).features;
  project = field: builtins.sort (a: b: a.order < b.order)
    (map (id: features.${id}.metadata.${field})
      (builtins.filter (id: features.${id}.metadata ? ${field}) (builtins.attrNames features)));
  names = entries: map (entry: entry.name) entries;
  toAttrs = entries: builtins.listToAttrs (map (value: { name = value.name; inherit value; }) entries);
  classifications = project "classifications";
  foundations = project "foundations";
  hardware = project "hardware";
  packages = project "package";
  roles = project "role";
in {
  inherit classifications foundations hardware packages roles;
  classificationsByName = toAttrs classifications;
  foundationsByName = toAttrs foundations;
  hardwareByName = toAttrs hardware;
  packagesByName = toAttrs packages;
  rolesByName = toAttrs roles;
  classificationNames = names classifications;
  foundationNames = names foundations;
  templateNames = map (foundation: foundation.template) foundations;
  homeHardwareNames = names (builtins.filter (entry: entry.homeManager) hardware);
  packageNames = names packages;
  roleNames = names roles;
  homeCompatibleRoleNames = names (builtins.filter (role: (role.homeCompatible or true)) roles);
}

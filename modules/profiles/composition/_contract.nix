{ catalog }: let
  loader = import ../../flake/features/_loader.nix {};
  inherit (loader) features;
  suffix = prefix: id: builtins.substring (builtins.stringLength prefix) (builtins.stringLength id) id;
  project = prefix: field: builtins.listToAttrs (map (id: {
    name = suffix prefix id; value = features.${id}.metadata.${field};
  }) (builtins.filter (id: features.${id}.metadata ? ${field}) (builtins.attrNames features)));
  targets = schema: id: prefix: map (suffix prefix)
    (builtins.filter (dep: builtins.substring 0 (builtins.stringLength prefix) dep == prefix) (loader.dependencies schema id));
  applications = project "apps/" "application";
  roles = builtins.mapAttrs (name: value: value // { capabilities = targets 3 "roles/${name}" "capabilities/"; }) (project "roles/" "role");
  capabilities = builtins.mapAttrs (name: value: value // { applications = targets 3 "capabilities/${name}" "apps/"; }) (project "capabilities/" "capability");
  base = features."home/base".metadata;
in {
  schema = 1; profileSchema = 3; status = "draft";
  inherit applications roles capabilities;
  inherit (base) commonCapabilities infrastructure graphics;
  optionalPackages = builtins.listToAttrs (map (name: { inherit name; value = name; }) catalog.packageNames);
}

let
  plans = import ./_plans.nix;
  loader = import ../flake/features/_loader.nix { };
  inherit (loader) features;
  root = ../..;
  files =
    relative:
    let
      entries = builtins.readDir (root + "/${relative}");
    in
    builtins.concatLists (
      map (
        name:
        let
          path = "${relative}/${name}";
        in
        if entries.${name} == "directory" then files path else [ path ]
      ) (builtins.attrNames entries)
    );
  selection = import ../profiles/composition/_selection.nix;
  profiles = builtins.fromJSON (builtins.readFile ./profiles/_cases.json);
  cases = builtins.mapAttrs (_: group: builtins.mapAttrs (_: selection) group) profiles;
  defaultProfile = builtins.fromJSON (builtins.readFile ../../profile.json);
  default = selection defaultProfile;
  check = roots: {
    schema = 3;
    inherit roots;
  };
in
{
  schema = 1;
  inherit plans;
  features = builtins.mapAttrs (id: f: {
    directory = "modules/${id}/";
    descriptorHash = builtins.hashString "sha256" (
      builtins.readFile (root + "/modules/${id}/_feature.nix")
    );
    files = files "modules/${id}";
    dependencies = f.dependencies;
    schemaDependencies = f.schemaDependencies;
  }) features;
  inherit cases;
  checks = {
    home = default;
    password-managers = check ["home/password-managers"];
    profile-command = default;
    nixgl-wrapper = selection (defaultProfile // { schema = 3; });
    desktop-icons = selection (
      defaultProfile
      // {
        schema = 3;
        roles = [ ];
        packages = [ ];
        capabilities = [ "desktop-comforts" ];
      }
    );
    profile-generation = check (builtins.attrNames features);
    check-flake-file = check [ ];
    ci-graph = check [ ];
    consumer-template = check [
      "flake/exports"
      "home/commands"
    ];
  };
  fullChecks = plans.full.checks;
}

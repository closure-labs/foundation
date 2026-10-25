{
  "id" = "apps/blender";
  "metadata" = {
    "application" = {
      "attribute" = "blender";
      "declaration" = "nix:nixpkgs:blender";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "blender";
      "declaration" = "nix:nixpkgs:blender";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
  };
  "dependencies" = [
    "providers/nixpkgs"
    "providers/graphics"
  ];
  "schemaDependencies" = { };
  configuration =
    schema:
    if schema == 3 then
      (import ../../profiles/composition/_application.nix {
        id = "blender";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
